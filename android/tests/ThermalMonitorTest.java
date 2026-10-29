package io.github.al90slj23.azerothsurvivors;

/** Contract checks for JS-facing units, absent/vendor-invalid readings, and all Android statuses. */
public final class ThermalMonitorTest {
    private static int checks;
    private static void equal(String expected, String actual) {
        checks++;
        if (!expected.equals(actual)) throw new AssertionError("Expected " + expected + ", got " + actual);
    }
    public static void main(String[] args) {
        equal("{\"batteryCelsius\":36.7,\"thermalStatus\":2}", ThermalMonitor.json(367, 2));
        equal("{\"batteryCelsius\":0.0,\"thermalStatus\":0}", ThermalMonitor.json(0, 0));
        equal("{\"batteryCelsius\":-10.5,\"thermalStatus\":1}", ThermalMonitor.json(-105, 1));
        equal(ThermalMonitor.UNAVAILABLE, ThermalMonitor.json(null, -1));
        equal(ThermalMonitor.UNAVAILABLE, ThermalMonitor.json(Integer.MIN_VALUE, -20));
        equal(ThermalMonitor.UNAVAILABLE, ThermalMonitor.json(1001, 7));
        equal(ThermalMonitor.UNAVAILABLE, ThermalMonitor.json(-401, Integer.MAX_VALUE));
        for (int status = 0; status <= 6; status++) {
            equal("{\"batteryCelsius\":null,\"thermalStatus\":" + status + "}", ThermalMonitor.json(null, status));
        }
        equal("{\"batteryCelsius\":100.0,\"thermalStatus\":-1}", ThermalMonitor.json(1000, -1));
        equal("{\"batteryCelsius\":-40.0,\"thermalStatus\":-1}", ThermalMonitor.json(-400, -1));
        System.out.println(checks + " thermal contract assertions passed");
    }
}
