package com.drifttank.game;

// =====================================================================
//  DriftNetPlugin  —  lets the Android app HOST a Drift Tank game
// =====================================================================
// The game itself runs as Python inside the app's WebView, and a WebView
// can't open ports. This small native piece does only the networking:
//
//   port 5757 : laptops   - one JSON message per line (same as network.py)
//   port 8080 : phones    - WebSocket. "/game" = the phone/web game app,
//                           anything else = the controller page (phone_page.html,
//                           also served on http://<ip>:8080/)
//
// Every connection gets a number (id). The plugin tells the game
//   "join"    {id, kind: "tcp" | "game" | "phone"}
//   "message" {id, data}
//   "leave"   {id}
// and the game answers with send / broadcast / kick. All game rules stay
// in Python (part1_engine/webnet.py WebHost).
// =====================================================================

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@CapacitorPlugin(name = "DriftNet")
public class DriftNetPlugin extends Plugin {

    private static final String MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

    private ServerSocket tcpServer;
    private ServerSocket wsServer;
    private String page = "<h1>Drift Tank</h1>";
    private final AtomicInteger nextId = new AtomicInteger(1);
    private final Map<Integer, Conn> conns = new ConcurrentHashMap<>();

    /** One connected laptop or phone. */
    private static class Conn {
        final Socket socket;
        final OutputStream out;
        final boolean websocket;

        Conn(Socket socket, boolean websocket) throws IOException {
            this.socket = socket;
            this.out = socket.getOutputStream();
            this.websocket = websocket;
        }

        synchronized void send(String text) {
            try {
                byte[] payload = text.getBytes(StandardCharsets.UTF_8);
                if (websocket) {
                    ByteArrayOutputStream frame = new ByteArrayOutputStream(payload.length + 10);
                    frame.write(0x81);                              // final frame, text
                    int n = payload.length;
                    if (n < 126) {
                        frame.write(n);
                    } else if (n < 65536) {
                        frame.write(126);
                        frame.write((n >> 8) & 0xFF);
                        frame.write(n & 0xFF);
                    } else {
                        frame.write(127);
                        for (int i = 7; i >= 0; i--) frame.write((int) (((long) n >> (8 * i)) & 0xFF));
                    }
                    frame.write(payload);
                    out.write(frame.toByteArray());
                } else {
                    out.write(payload);
                    out.write('\n');
                }
                out.flush();
            } catch (IOException e) {
                close();
            }
        }

        void close() {
            try { socket.close(); } catch (IOException ignored) { }
        }
    }

    // ------------------------------------------------------------------
    //  methods the game calls
    // ------------------------------------------------------------------
    @PluginMethod
    public void start(PluginCall call) {
        int tcpPort = call.getInt("tcpPort", 5757);
        int wsPort = call.getInt("wsPort", 8080);
        String html = call.getString("page");
        if (html != null) page = html;
        stopServers();
        try {
            tcpServer = new ServerSocket(tcpPort);
            tcpServer.setReuseAddress(true);
            wsServer = new ServerSocket(wsPort);
            wsServer.setReuseAddress(true);
        } catch (IOException e) {
            stopServers();
            call.reject("Port busy: " + e.getMessage());
            return;
        }
        final ServerSocket tcp = tcpServer;
        final ServerSocket ws = wsServer;
        new Thread(() -> acceptLoop(tcp, false), "drift-tcp").start();
        new Thread(() -> acceptLoop(ws, true), "drift-ws").start();
        JSObject result = new JSObject();
        result.put("ip", lanIp());
        call.resolve(result);
    }

    @PluginMethod
    public void send(PluginCall call) {
        Conn conn = conns.get(call.getInt("id", -1));
        String data = call.getString("data", "");
        if (conn != null) conn.send(data);
        call.resolve();
    }

    @PluginMethod
    public void broadcast(PluginCall call) {
        String data = call.getString("data", "");
        JSArray ids = call.getArray("ids");
        try {
            for (int i = 0; ids != null && i < ids.length(); i++) {
                Conn conn = conns.get(ids.getInt(i));
                if (conn != null) conn.send(data);
            }
        } catch (Exception ignored) { }
        call.resolve();
    }

    @PluginMethod
    public void kick(PluginCall call) {
        Conn conn = conns.get(call.getInt("id", -1));
        if (conn != null) conn.close();
        call.resolve();
    }

    @PluginMethod
    public void stop(PluginCall call) {
        stopServers();
        call.resolve();
    }

    @PluginMethod
    public void ip(PluginCall call) {
        JSObject result = new JSObject();
        result.put("ip", lanIp());
        call.resolve(result);
    }

    @Override
    protected void handleOnDestroy() {
        stopServers();
    }

    // ------------------------------------------------------------------
    //  servers
    // ------------------------------------------------------------------
    private void stopServers() {
        try { if (tcpServer != null) tcpServer.close(); } catch (IOException ignored) { }
        try { if (wsServer != null) wsServer.close(); } catch (IOException ignored) { }
        tcpServer = null;
        wsServer = null;
        for (Conn c : conns.values()) c.close();
        conns.clear();
    }

    private void acceptLoop(ServerSocket server, boolean websocket) {
        while (!server.isClosed()) {
            try {
                Socket socket = server.accept();
                socket.setTcpNoDelay(true);
                new Thread(() -> {
                    if (websocket) handleWebSocketPort(socket);
                    else handleTcp(socket);
                }, "drift-conn").start();
            } catch (IOException e) {
                break;
            }
        }
    }

    private void emit(String event, int id, String key, String value) {
        JSObject data = new JSObject();
        data.put("id", id);
        if (key != null) data.put(key, value);
        notifyListeners(event, data);
    }

    private void finish(int id, Conn conn) {
        conn.close();
        if (conns.remove(id) != null) emit("leave", id, null, null);
    }

    /** Laptops: JSON lines. */
    private void handleTcp(Socket socket) {
        int id = nextId.getAndIncrement();
        Conn conn;
        try {
            conn = new Conn(socket, false);
        } catch (IOException e) {
            return;
        }
        conns.put(id, conn);
        emit("join", id, "kind", "tcp");
        try {
            BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.isEmpty()) emit("message", id, "data", line);
            }
        } catch (IOException ignored) { }
        finish(id, conn);
    }

    /** Phones: plain HTTP (controller page) or WebSocket (game app / controller). */
    private void handleWebSocketPort(Socket socket) {
        try {
            InputStream in = socket.getInputStream();
            String head = readHead(in);
            if (head == null) { socket.close(); return; }
            String[] lines = head.split("\r\n");
            String[] first = lines[0].split(" ");
            String path = first.length > 1 ? first[1] : "/";
            Map<String, String> headers = new HashMap<>();
            for (int i = 1; i < lines.length; i++) {
                int colon = lines[i].indexOf(':');
                if (colon > 0) headers.put(lines[i].substring(0, colon).trim().toLowerCase(), lines[i].substring(colon + 1).trim());
            }
            OutputStream out = socket.getOutputStream();
            if (!"websocket".equalsIgnoreCase(headers.getOrDefault("upgrade", ""))) {
                byte[] body = ("/".equals(path) || "/index.html".equals(path) ? page : "not found").getBytes(StandardCharsets.UTF_8);
                String status = body.length > 9 ? "200 OK" : "404 Not Found";
                out.write(("HTTP/1.1 " + status + "\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: " + body.length
                        + "\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n").getBytes(StandardCharsets.UTF_8));
                out.write(body);
                out.flush();
                socket.close();
                return;
            }
            String key = headers.getOrDefault("sec-websocket-key", "");
            MessageDigest sha1 = MessageDigest.getInstance("SHA-1");
            String accept = android.util.Base64.encodeToString(
                    sha1.digest((key + MAGIC).getBytes(StandardCharsets.UTF_8)), android.util.Base64.NO_WRAP);
            out.write(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: "
                    + accept + "\r\n\r\n").getBytes(StandardCharsets.UTF_8));
            out.flush();

            int id = nextId.getAndIncrement();
            Conn conn = new Conn(socket, true);
            conns.put(id, conn);
            emit("join", id, "kind", path.startsWith("/game") ? "game" : "phone");
            try {
                while (true) {
                    String text = readFrame(in, conn);
                    if (text == null) break;
                    if (!text.isEmpty()) emit("message", id, "data", text);
                }
            } catch (IOException ignored) { }
            finish(id, conn);
        } catch (Exception e) {
            try { socket.close(); } catch (IOException ignored) { }
        }
    }

    private static String readHead(InputStream in) throws IOException {
        ByteArrayOutputStream head = new ByteArrayOutputStream();
        int matched = 0;
        while (head.size() < 16000) {
            int b = in.read();
            if (b < 0) return null;
            head.write(b);
            matched = (b == "\r\n\r\n".charAt(matched)) ? matched + 1 : (b == '\r' ? 1 : 0);
            if (matched == 4) return head.toString("UTF-8");
        }
        return null;
    }

    private static byte[] readExact(InputStream in, int n) throws IOException {
        byte[] data = new byte[n];
        int got = 0;
        while (got < n) {
            int r = in.read(data, got, n - got);
            if (r < 0) throw new IOException("closed");
            got += r;
        }
        return data;
    }

    /** Next text message, "" for control frames, null when the phone disconnects. */
    private static String readFrame(InputStream in, Conn conn) throws IOException {
        byte[] h = readExact(in, 2);
        int opcode = h[0] & 0x0F;
        long length = h[1] & 0x7F;
        if (length == 126) {
            byte[] ext = readExact(in, 2);
            length = ((ext[0] & 0xFF) << 8) | (ext[1] & 0xFF);
        } else if (length == 127) {
            byte[] ext = readExact(in, 8);
            length = 0;
            for (byte b : ext) length = (length << 8) | (b & 0xFF);
        }
        if (length > 1_000_000) return null;
        byte[] mask = (h[1] & 0x80) != 0 ? readExact(in, 4) : new byte[]{0, 0, 0, 0};
        byte[] data = readExact(in, (int) length);
        for (int i = 0; i < data.length; i++) data[i] ^= mask[i % 4];
        if (opcode == 0x8) return null;                       // close
        if (opcode == 0x9) {                                  // ping -> pong
            synchronized (conn) {
                conn.out.write(new byte[]{(byte) 0x8A, (byte) data.length});
                conn.out.write(data);
                conn.out.flush();
            }
            return "";
        }
        if (opcode == 0x1 || opcode == 0x0) return new String(data, StandardCharsets.UTF_8);
        return "";
    }

    /** This phone's address on the Wi-Fi (what others type to join). */
    private static String lanIp() {
        try {
            String fallback = "";
            for (NetworkInterface nif : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                if (!nif.isUp() || nif.isLoopback()) continue;
                for (InetAddress addr : Collections.list(nif.getInetAddresses())) {
                    if (addr instanceof Inet4Address && addr.isSiteLocalAddress()) {
                        String name = nif.getName();
                        if (name.startsWith("wlan") || name.startsWith("ap") || name.startsWith("swlan")) {
                            return addr.getHostAddress();     // Wi-Fi or hotspot first
                        }
                        if (fallback.isEmpty()) fallback = addr.getHostAddress();
                    }
                }
            }
            return fallback;
        } catch (Exception e) {
            return "";
        }
    }
}
