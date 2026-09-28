plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "ai.openvq"
    compileSdk = 35
    ndkVersion = "27.0.12077973"

    defaultConfig {
        minSdk = 24
        externalNativeBuild { cmake { cppFlags += "-std=c++17" } }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }
}

kotlin {
    jvmToolchain(17)
}


dependencies {
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.30.0")
}
