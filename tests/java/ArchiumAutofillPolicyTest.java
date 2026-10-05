import org.chromium.chrome.browser.autofill.ArchiumAutofillPolicy;

public final class ArchiumAutofillPolicyTest {
    public static void main(String[] args) {
        if (!ArchiumAutofillPolicy.mustUseInternalGoogleProvider("org.chromium.chrome", true))
            throw new AssertionError("Chromium behavior must be preserved");
        if (!ArchiumAutofillPolicy.mustUseInternalGoogleProvider("com.android.chrome", true))
            throw new AssertionError("Chrome behavior must be preserved");
        if (ArchiumAutofillPolicy.mustUseInternalGoogleProvider("app.archium.android", true))
            throw new AssertionError("Archium must allow its selected Google platform provider");
        if (ArchiumAutofillPolicy.mustUseInternalGoogleProvider("app.archium.android", false))
            throw new AssertionError("Alternative providers remain eligible");
        System.out.println("ArchiumAutofillPolicy: provider routing tests passed");
    }
}
