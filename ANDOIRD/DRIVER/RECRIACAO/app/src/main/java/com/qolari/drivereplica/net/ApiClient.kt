package com.qolari.drivereplica.net

import com.google.gson.Gson
import com.google.gson.JsonSyntaxException
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import com.qolari.drivereplica.config.AppConfig
import java.util.concurrent.TimeUnit

object ApiClient {

    private val gson = Gson()

    fun create(baseUrl: String, tokenProvider: () -> String?): DriverApi {
        val http = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val token = tokenProvider().orEmpty()
                chain.proceed(
                    chain.request().newBuilder()
                        .header("Content-Type", "application/json")
                        .apply {
                            if (token.isNotEmpty()) {
                                AppConfig.tokenHeaders.forEach { header(it, token) }
                            }
                        }
                        .build()
                )
            }
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
            })
            .connectTimeout(AppConfig.CONNECT_TIMEOUT_S, TimeUnit.SECONDS)
            .readTimeout(AppConfig.READ_TIMEOUT_S, TimeUnit.SECONDS)
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl.trimEnd('/') + "/")
            .client(http)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
            .create(DriverApi::class.java)
    }

    /** Mensagem de erro no formato da edge: {"code":"rtapi.x","message":"..."} */
    fun errorMessage(e: Throwable): String {
        if (e is HttpException) {
            try {
                val raw = e.response()?.errorBody()?.string()
                val err = raw?.let { gson.fromJson(it, ApiError::class.java) }
                if (err?.message != null) return err.message
            } catch (_: Exception) {
            }
            return "Erro ${e.code()}"
        }
        return e.message ?: "Erro de rede"
    }
}
