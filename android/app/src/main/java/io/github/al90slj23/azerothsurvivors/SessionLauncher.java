package io.github.al90slj23.azerothsurvivors;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Browser;
import android.widget.Toast;

/** Chrome is a visible, standards-based fallback, without TWA verification bypasses. */
final class SessionLauncher {
    private static final String[] CHROME_PACKAGES = {
            "com.android.chrome", "com.chrome.beta", "com.chrome.dev", "com.chrome.canary"
    };

    static boolean openGame(Activity activity) {
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(GameService.ORIGIN + "/"));
        Bundle options = new Bundle();
        options.putBinder("android.support.customtabs.extra.SESSION", null);
        intent.putExtras(options);
        intent.putExtra("android.support.customtabs.extra.TOOLBAR_COLOR", 0xff10100d);
        intent.putExtra("android.support.customtabs.extra.TITLE_VISIBILITY", 0);
        intent.putExtra("android.support.customtabs.extra.ENABLE_URLBAR_HIDING", true);
        intent.putExtra("androidx.browser.customtabs.extra.SHARE_STATE", 2);
        intent.putExtra(Browser.EXTRA_APPLICATION_ID, activity.getPackageName());
        for (String name : CHROME_PACKAGES) {
            Intent candidate = new Intent(intent).setPackage(name);
            if (activity.getPackageManager().resolveActivity(candidate, 0) != null) {
                try { activity.startActivity(candidate); return true; }
                catch (ActivityNotFoundException ignored) { /* Try another installed Chrome. */ }
            }
        }
        Toast.makeText(activity, "未找到 Chrome，请先安装或更新 Chrome 后重试", Toast.LENGTH_LONG).show();
        return false;
    }

    static void openOfficial(Activity activity, Uri uri) {
        if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getUserInfo() != null) return;
        String host = uri.getHost();
        if (!("wow.aethus.pl".equalsIgnoreCase(host) || "discord.gg".equalsIgnoreCase(host)
                || "discord.com".equalsIgnoreCase(host))) return;
        if (uri.getPort() != -1 && uri.getPort() != 443) return;
        try { activity.startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
        catch (ActivityNotFoundException ignored) {
            Toast.makeText(activity, "没有可打开此链接的浏览器", Toast.LENGTH_SHORT).show();
        }
    }

    private SessionLauncher() {}
}
