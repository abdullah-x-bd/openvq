package ai.openvq

object OpenVqNative {
    init { System.loadLibrary("openvq_android") }

    /** Returns the same JSON schema as the native CLI. */
    external fun analyzePcm16(reference: ShortArray, degraded: ShortArray, sampleRate: Int): String
}
