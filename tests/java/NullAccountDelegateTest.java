import org.chromium.components.signin.NullAccountManagerDelegate;

public final class NullAccountDelegateTest {
    public static void main(String[] args) {
        int[] calls = {0};
        new NullAccountManagerDelegate().createAddAccountIntent(null, intent -> {
            if (intent != null) throw new AssertionError("Unavailable backend must not claim an intent");
            calls[0]++;
        });
        if (calls[0] != 1) throw new AssertionError("Callback must run exactly once");
        System.out.println("NullAccountManagerDelegate: unavailable account operation reported without exception");
    }
}
