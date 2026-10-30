import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import java.util.Properties

// Chaves e caminhos locais vivem em local.properties (nunca no codigo): MAPS_API_KEY entra no manifest (lote 2).
val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

plugins {
    id("com.android.application")
    // Compose so para os ecras que a original faz em Compose (ux_capture/toolkit_por_ecra.csv, STACK_DECISAO.md).
    id("org.jetbrains.kotlin.plugin.compose") version "2.2.10"
}

android {
    namespace = "com.qolari.drivereplica"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.qolari.drivereplica"
        minSdk = 29
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
        manifestPlaceholders["MAPS_API_KEY"] = localProps.getProperty("MAPS_API_KEY", "")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
    buildFeatures {
        viewBinding = true
        compose = true
        buildConfig = true
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlin {
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_17)
        }
    }
}

// ConfigTest varre src/main em tempo de execucao (zero hosts fora de AppConfig.kt): sem isto o Gradle
// dava os testes como "up-to-date" mesmo depois de alterar o codigo-fonte.
tasks.withType<Test>().configureEach {
    inputs.dir("src/main").withPathSensitivity(PathSensitivity.RELATIVE)
}

dependencies {
    // UI (Views). Compose entra no lote 1, so para os ecras que a original faz em Compose (STACK_DECISAO.md).
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("androidx.appcompat:appcompat:1.7.1")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.2.1")
    implementation("androidx.fragment:fragment-ktx:1.8.9")
    implementation("androidx.activity:activity-ktx:1.10.1")
    implementation("androidx.navigation:navigation-fragment-ktx:2.9.4")
    implementation("androidx.navigation:navigation-ui-ktx:2.9.4")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.9.4")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.9.4")
    implementation("androidx.datastore:datastore-preferences:1.1.7")
    implementation("androidx.recyclerview:recyclerview:1.4.0")
    implementation("androidx.swiperefreshlayout:swiperefreshlayout:1.1.0")
    // Mapas reais (Maps SDK for Android), com a chave em local.properties.
    implementation("com.google.android.gms:play-services-maps:20.1.0")

    // Compose (ilhas hospedadas em Fragments por ComposeView)
    implementation(platform("androidx.compose:compose-bom:2025.06.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")

    // Rede e dados (equivalentes da original: Retrofit + OkHttp + Gson + Coroutines)
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("com.google.code.gson:gson:2.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
}
