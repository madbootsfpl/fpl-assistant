import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// ⭐⭐ **The release signing key, read from a file that is never committed** (ADR-278).
//
// ⚠️⚠️ `key.properties` holds the keystore password and is gitignored by Flutter's own template. The
// keystore itself (`~/madboots-release.jks`) is the app's identity: an APK signed with one key can
// **never** be updated by a build signed with another, so losing it means never shipping an update to
// anyone who has already installed.
val keystoreProperties = Properties().apply {
    val f = rootProject.file("key.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

android {
    namespace = "com.madboots.fpl"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.madboots.fpl"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        // Uses the version code from pubspec.yaml. When using split APKs, 1000 * ABI_VERSION
        // is added automatically by Flutter. (https://developer.android.com/studio/build/configure-apk-splits#configure-APK-versions)
        // You can force using the value of versionCode by specifying the `-P force-version-code-ignoring-abi=true`
        // flag during build.
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            keyAlias = keystoreProperties.getProperty("keyAlias")
            keyPassword = keystoreProperties.getProperty("keyPassword")
            storeFile = keystoreProperties.getProperty("storeFile")?.let { file(it) }
            storePassword = keystoreProperties.getProperty("storePassword")

            // ⭐⭐ **v3 costs nothing and is the only hedge against the one unrecoverable mistake here.**
            // Losing the keystore means never updating the app again — v3 is the scheme that supports
            // **key rotation**, so a future key can prove it succeeds this one. ⚠️ *It has to be in the
            // APKs people already installed*: rotation proves a chain from the key they trust, and a
            // build signed v2-only can never start that chain.
            enableV2Signing = true
            enableV3Signing = true
        }
    }

    buildTypes {
        release {
            // ⚠️⚠️ **It fails rather than falling back to the debug key**, and that is the whole point.
            //
            // Flutter's template signs release builds with the **debug** key so `flutter run --release`
            // works out of the box. ⭐ *A fallback that silently produces an installable artefact is how
            // a debug-signed APK reaches a tester* — and once it does, every future properly-signed
            // update is refused by Android, so the only way forward is uninstall-and-reinstall, which
            // wipes their saved drafts.
            //
            // ⭐ A build that stops is a build you fix. A build that quietly signs with the wrong key is
            // one you discover months later, from the one person who cannot update.
            if (keystoreProperties.isEmpty) {
                throw GradleException(
                    "Release build needs android/key.properties (storeFile, storePassword, " +
                    "keyAlias, keyPassword). See docs/03_Architecture/Android_Builds.md. " +
                    "Debug builds are unaffected."
                )
            }
            signingConfig = signingConfigs.getByName("release")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
