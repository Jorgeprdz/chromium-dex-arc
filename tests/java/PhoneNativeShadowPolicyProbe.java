// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.testing.local;

import java.lang.reflect.InvocationTargetException;
import java.nio.file.Path;
import java.util.HashSet;
import org.junit.Test;
import org.junit.runner.Description;

/** Runs the pinned Chromium shadow policy on the delivered test annotations, before local JUnit. */
public class PhoneNativeShadowPolicyProbe {
    public static void main(String[] args) throws Exception {
        var computer = new TestListComputer(Allowlist.fromFile(Path.of(args[0])));
        var compute = TestListComputer.class.getDeclaredMethod(
                "computeConfig", Description.class, java.util.Set.class, java.util.Set.class);
        compute.setAccessible(true);
        int count = 0;
        for (String name : new String[] {"ArcPhoneNavigationTest", "ArcPhoneGlassTest"}) {
        var clazz = Class.forName("org.chromium.chrome.browser.arc." + name);
        for (var method : clazz.getDeclaredMethods()) {
            if (!method.isAnnotationPresent(Test.class)) continue;
            var description = Description.createTestDescription(clazz, method.getName(), method.getAnnotations());
            try {
                compute.invoke(computer, description, new HashSet<String>(), new HashSet<String>());
            } catch (InvocationTargetException error) {
                throw new AssertionError("Pinned Chromium test discovery rejected " + method.getName(), error.getCause());
            }
            count++;
        }
        }
        if (count == 0) throw new AssertionError("No delivered tests checked");
        System.out.println("PINNED_CHROMIUM_SHADOW_POLICY=PASS methods=" + count);
    }
}
