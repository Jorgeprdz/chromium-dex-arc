Pinned Chromium supplier API fixture, unmodified upstream source (BSD header retained).

Revision: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
Source: https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/base/android/java/src/org/chromium/base/supplier/MonotonicObservableSupplier.java

The host regression checks the fixture SHA-256 and compiles the delivered bookmark
registration against observer declarations extracted from this source. Coordinator
and callback-controller dependencies are synthetic boundaries. This gate does not
compile the entire native coordinator or demonstrate physical bookmark behavior.
