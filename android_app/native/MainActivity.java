package com.drifttank.game;

import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

/** The Android app's only screen: the web version in a WebView, plus our DriftNet plugin. */
public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(DriftNetPlugin.class);       // must be before super.onCreate
        super.onCreate(savedInstanceState);
    }
}
