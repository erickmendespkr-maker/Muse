package io.zer0.muse.ui.speech

import java.text.Normalizer
import java.util.Locale

/** Local transcript gate for Denise. This is NOT an always-on microphone detector. */
object DeniseWakeWord {
    const val KEYWORD = "denise"

    fun extractCommand(transcript: String): String? {
        val normalized = Normalizer.normalize(transcript.lowercase(Locale.ROOT), Normalizer.Form.NFD)
            .replace(Regex("\\p{M}+"), "")
        val match = Regex("(?:^|[^\\p{L}\\p{N}])denise(?=$|[^\\p{L}\\p{N}])").find(normalized)
            ?: return null
        return transcript.substring(match.range.last + 1).trimStart(' ', ',', '.', ':', ';', '!', '?', '-')
    }
}
