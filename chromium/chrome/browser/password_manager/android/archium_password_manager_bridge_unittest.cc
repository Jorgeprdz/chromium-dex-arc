// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// REAL_CONTRACT_TEST: exercises Chromium 157's actual TestingProfile/OTR
// identity rather than an artificial isIncognito boolean. NOT_EXECUTED.
#include "chrome/browser/password_manager/android/archium_password_manager_bridge.h"

#include "chrome/browser/profiles/profile.h"
#include "chrome/test/base/testing_profile.h"
#include "testing/gtest/include/gtest/gtest.h"

TEST(ArchiumPasswordManagerBridgeTest, NullProfileFailsClosed) {
  EXPECT_FALSE(ArchiumPasswordManagerBridge::CanManageProfile(nullptr));
}

TEST(ArchiumPasswordManagerBridgeTest, RealRegularProfileIsEligible) {
  TestingProfile regular;
  ASSERT_FALSE(regular.IsOffTheRecord());
  EXPECT_TRUE(ArchiumPasswordManagerBridge::CanManageProfile(&regular));
}

TEST(ArchiumPasswordManagerBridgeTest, RealOTRProfileCannotUnwrapIntoVault) {
  TestingProfile regular;
  Profile* off_the_record = regular.GetPrimaryOTRProfile(/*create_if_needed=*/true);
  ASSERT_NE(nullptr, off_the_record);
  ASSERT_TRUE(off_the_record->IsOffTheRecord());
  ASSERT_EQ(off_the_record->GetOriginalProfile(), &regular);
  EXPECT_FALSE(ArchiumPasswordManagerBridge::CanManageProfile(off_the_record));
  EXPECT_TRUE(ArchiumPasswordManagerBridge::CanManageProfile(&regular));
}
// SIMULATED_BOUNDARY: tests the exact handle registry used by native JNI
// dispatch, but with a synthetic receiver instead of a Java/JNI peer.
TEST(ArchiumPasswordManagerBridgeTest, OpaqueHandleNeverReusedAfterDestroy) {
  ArchiumNonReusingHandleMap<int> registry;
  EXPECT_FALSE(registry.Acquire(0));
  EXPECT_FALSE(registry.Acquire(-1));
  EXPECT_FALSE(registry.Acquire(123456));
  EXPECT_EQ(0, registry.Insert({}));

  int64_t first_handle = registry.Insert(std::make_shared<int>(42));
  ASSERT_GT(first_handle, 0);
  auto in_flight = registry.Acquire(first_handle);
  ASSERT_TRUE(in_flight);
  EXPECT_EQ(42, *in_flight);
  registry.Remove(first_handle);
  registry.Remove(first_handle);
  EXPECT_FALSE(registry.Acquire(first_handle));
  EXPECT_EQ(42, *in_flight);  // Receiver remains alive for in-flight dispatch.

  int64_t second_handle = registry.Insert(std::make_shared<int>(43));
  EXPECT_GT(second_handle, first_handle);
  EXPECT_FALSE(registry.Acquire(first_handle));
  ASSERT_TRUE(registry.Acquire(second_handle));
  EXPECT_EQ(43, *registry.Acquire(second_handle));
}
