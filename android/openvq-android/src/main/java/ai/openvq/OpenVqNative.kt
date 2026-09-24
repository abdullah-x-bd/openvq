package ai.openvq

object OpenVqNative {
    init { System.loadLibrary("openvq_android") }

    /** Returns the native diagnostic path without the external Phase-3 experts. */
    external fun analyzePcm16(reference: ShortArray, degraded: ShortArray, sampleRate: Int): String

    /**
     * Runs the frozen Phase-3 candidate. The caller supplies Google ViSQOL
     * v3.3.3 speech-mode and audio-mode MOS-LQO values for the same pair.
     */
    external fun analyzePcm16Hybrid(
        reference: ShortArray,
        degraded: ShortArray,
        sampleRate: Int,
        visqolSpeechMos: Double,
        visqolAudioMos: Double
    ): String
}
