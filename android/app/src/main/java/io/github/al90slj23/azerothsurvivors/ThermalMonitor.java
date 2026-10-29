package io.github.al90slj23.azerothsurvivors;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Build;
import android.os.PowerManager;

/** Event-driven, permission-free battery and system throttling readings. Not a CPU thermometer. */
final class ThermalMonitor implements AutoCloseable {
    static final String UNAVAILABLE = "{\"batteryCelsius\":null,\"thermalStatus\":-1}";
    private final Context context;
    private final PowerManager power;
    // Lifecycle and callbacks run on the main thread; JavaBridge only reads this immutable snapshot.
    private volatile String snapshot = UNAVAILABLE;
    private Integer batteryTenths;
    private int thermalStatus = -1;
    private boolean batteryRegistered;
    private boolean thermalRegistered;
    private boolean closed;
    private final BroadcastReceiver batteryReceiver = new BroadcastReceiver() {
        @Override public void onReceive(Context ignored, Intent intent) {
            if (!closed && intent != null && Intent.ACTION_BATTERY_CHANGED.equals(intent.getAction())) {
                readBattery(intent);
            }
        }
    };
    private final PowerManager.OnThermalStatusChangedListener thermalListener = status -> {
        if (!closed) { thermalStatus = validStatus(status); publish(); }
    };

    ThermalMonitor(Context owner) {
        context = owner.getApplicationContext();
        power = context.getSystemService(PowerManager.class);
        IntentFilter filter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        try {
            // BATTERY_CHANGED is a protected system-UID broadcast. Do not accept app senders.
            Intent initial;
            if (Build.VERSION.SDK_INT >= 33) {
                initial = context.registerReceiver(batteryReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
            } else initial = context.registerReceiver(batteryReceiver, filter);
            batteryRegistered = true;
            if (initial != null) readBattery(initial);
        } catch (RuntimeException ignored) { /* Some vendor devices do not expose a battery reading. */ }
        if (power != null) {
            try { thermalStatus = validStatus(power.getCurrentThermalStatus()); }
            catch (RuntimeException ignored) { thermalStatus = -1; }
            try {
                power.addThermalStatusListener(context.getMainExecutor(), thermalListener);
                thermalRegistered = true;
            } catch (RuntimeException ignored) { /* Keep the initial reading when events are unavailable. */ }
        }
        publish();
    }

    private void readBattery(Intent intent) {
        boolean present = intent.getBooleanExtra(BatteryManager.EXTRA_PRESENT, true);
        int raw = intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, Integer.MIN_VALUE);
        batteryTenths = present && intent.hasExtra(BatteryManager.EXTRA_TEMPERATURE) && validTemperature(raw)
                ? raw : null;
        publish();
    }

    private void publish() { snapshot = json(batteryTenths, thermalStatus); }

    String snapshot() { return snapshot; }

    static int validStatus(int status) { return status >= 0 && status <= 6 ? status : -1; }

    static boolean validTemperature(int tenths) { return tenths >= -400 && tenths <= 1000; }

    static String json(Integer tenths, int status) {
        String celsius = tenths != null && validTemperature(tenths) ? Float.toString(tenths / 10.0f) : "null";
        return "{\"batteryCelsius\":" + celsius + ",\"thermalStatus\":" + validStatus(status) + "}";
    }

    @Override public void close() {
        if (closed) return;
        closed = true;
        if (batteryRegistered) {
            try { context.unregisterReceiver(batteryReceiver); } catch (RuntimeException ignored) { }
            batteryRegistered = false;
        }
        if (thermalRegistered && power != null) {
            try { power.removeThermalStatusListener(thermalListener); } catch (RuntimeException ignored) { }
            thermalRegistered = false;
        }
        batteryTenths = null;
        thermalStatus = -1;
        snapshot = UNAVAILABLE;
    }
}
