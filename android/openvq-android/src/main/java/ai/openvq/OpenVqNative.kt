package ai.openvq

object OpenVqNative {
    init {
        System.loadLibrary("openvq_android")
    }

    /** Native diagnostics with the current repaired frontend. */
    external fun analyzePcm16(
        reference: ShortArray,
        degraded: ShortArray,
        sampleRate: Int
    ): String

    /** Full Phase 6 trace JSON for parity/debug tooling. */
    external fun tracePcm16(
        reference: ShortArray,
        degraded: ShortArray,
        sampleRate: Int
    ): String

    /** Historical frozen Phase 3 hybrid reproduction. */
    external fun analyzePcm16Hybrid(
        reference: ShortArray,
        degraded: ShortArray,
        sampleRate: Int,
        visqolSpeechMos: Double,
        visqolAudioMos: Double
    ): String

    /** Historical native-first Phase 4 candidate. */
    external fun analyzePcm16Phase4(
        reference: ShortArray,
        degraded: ShortArray,
        sampleRate: Int
    ): String

    external fun analyzePcm16Phase4WithExperts(
        reference: ShortArray,
        degraded: ShortArray,
        sampleRate: Int,
        visqolSpeechMos: Double,
        visqolAudioMos: Double
    ): String
}
