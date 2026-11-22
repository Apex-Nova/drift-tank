// =====================================================================
//  Drift Tank relay  —  lets players on different networks play together
// =====================================================================
// The game itself still runs on the HOST's device (exactly like LAN play).
// This server only passes messages along, in "rooms" with a 5-digit code:
//
//   host   connects to  wss://<relay>/host            -> gets {"k":"hosting","code":"48213"}
//   player connects to  wss://<relay>/join/48213?kind=game
//
//   player -> host : the player's text is wrapped  {"k":"msg","id":3,"d":"<text>"}
//   host -> player : host sends {"to":[3,4],"d":"<text>"}  -> each player gets "<text>"
//   host also hears {"k":"join","id":3,"kind":"game"} and {"k":"leave","id":3}
//
// That is the same event list the Android app's native plugin produces, so the
// Python side (part1_engine/webnet.py WebHost) works with both.
// One Durable Object = one room (Cloudflare keeps it in one place in memory).
// =====================================================================
import { DurableObject } from "cloudflare:workers";

const MAX_PLAYERS = 8;
const MAX_MESSAGE = 64 * 1024;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/" || url.pathname === "/health") {
      return new Response("Drift Tank relay is running", { headers: { "content-type": "text/plain" } });
    }
    if (request.headers.get("Upgrade") !== "websocket") {
      return new Response("WebSocket expected", { status: 426 });
    }
    if (url.pathname === "/host") {
      for (let attempt = 0; attempt < 10; attempt++) {
        const code = String(Math.floor(10000 + Math.random() * 90000));
        const response = await roomFor(env, code).fetch(withRoom(request, code, "host"));
        if (response.status !== 409) return response;      // 409 = code already in use, try another
      }
      return new Response("No free room", { status: 503 });
    }
    const join = url.pathname.match(/^\/join\/(\d{5})$/);
    if (join) {
      return roomFor(env, join[1]).fetch(withRoom(request, join[1], url.searchParams.get("kind") || "game"));
    }
    return new Response("Not found", { status: 404 });
  },
};

function roomFor(env, code) {
  return env.ROOMS.get(env.ROOMS.idFromName(code));
}

function withRoom(request, code, role) {
  const copy = new Request(request);
  copy.headers.set("X-Room", code);
  copy.headers.set("X-Role", role);
  return copy;
}

function safeSend(ws, text) {
  try { ws.send(text); } catch (e) { /* already closed */ }
}

export class Room extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.host = null;
    this.players = new Map();      // id -> WebSocket
    this.nextId = 1;
  }

  async fetch(request) {
    const code = request.headers.get("X-Room");
    const role = request.headers.get("X-Role");
    if (role === "host") {
      if (this.host) return new Response("Room in use", { status: 409 });
      return this.acceptHost(code);
    }
    if (!this.host) return new Response("No such room", { status: 404 });
    if (this.players.size >= MAX_PLAYERS) return new Response("Room full", { status: 403 });
    return this.acceptPlayer(role === "phone" ? "phone" : "game");
  }

  acceptHost(code) {
    const [client, server] = Object.values(new WebSocketPair());
    server.accept();
    this.host = server;
    safeSend(server, JSON.stringify({ k: "hosting", code: code }));
    server.addEventListener("message", (event) => {
      if (typeof event.data !== "string" || event.data.length > MAX_MESSAGE) return;
      let message;
      try { message = JSON.parse(event.data); } catch (e) { return; }
      if (Array.isArray(message.to) && typeof message.d === "string") {
        for (const id of message.to) {
          const ws = this.players.get(id);
          if (ws) safeSend(ws, message.d);
        }
      } else if (message.kick !== undefined) {
        const ws = this.players.get(message.kick);
        if (ws) { try { ws.close(1000, "kicked"); } catch (e) {} }
        this.players.delete(message.kick);
      }
    });
    const closeRoom = () => {
      if (this.host !== server) return;
      this.host = null;
      for (const ws of this.players.values()) {
        try { ws.close(1001, "host left"); } catch (e) {}
      }
      this.players.clear();
    };
    server.addEventListener("close", closeRoom);
    server.addEventListener("error", closeRoom);
    return new Response(null, { status: 101, webSocket: client });
  }

  acceptPlayer(kind) {
    const [client, server] = Object.values(new WebSocketPair());
    server.accept();
    const id = this.nextId++;
    this.players.set(id, server);
    safeSend(this.host, JSON.stringify({ k: "join", id: id, kind: kind }));
    server.addEventListener("message", (event) => {
      if (typeof event.data !== "string" || event.data.length > MAX_MESSAGE || !this.host) return;
      safeSend(this.host, JSON.stringify({ k: "msg", id: id, d: event.data }));
    });
    const leave = () => {
      if (!this.players.has(id)) return;
      this.players.delete(id);
      if (this.host) safeSend(this.host, JSON.stringify({ k: "leave", id: id }));
    };
    server.addEventListener("close", leave);
    server.addEventListener("error", leave);
    return new Response(null, { status: 101, webSocket: client });
  }
}
