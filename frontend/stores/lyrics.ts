import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useLyricsStore = defineStore('lyrics', () => {
  const lyricText = ref('');

  // Parse marked up lyrics into segments.
  // Line breaks separate segments.
  // Double line breaks separate screens.
  // Underscores separate segments on word boundaries between a line.
  // Slashes separate segments within a word.
  const lyricSegments = computed(() => {
    const segments = [];
    let currentSegment = '';

    for (let i = 0; i < lyricText.value.length; i++) {
      let finishSegment = false;
      const char = lyricText.value[i];
      if (['\n', '/', '_'].includes(char) || i == lyricText.value.length - 1) {
        finishSegment = true;
      }
      if (char == '\n' && currentSegment == '') {
        segments[segments.length - 1].text += char;
        continue;
      }
      currentSegment += char;
      if (finishSegment) {
        segments.push({
          text: currentSegment,
        });
        currentSegment = '';
      }
    }

    return segments;
  });

  function setLyrics(text: string) {
    lyricText.value = text;
  }

  return {
    lyricText,
    lyricSegments,
    setLyrics
  };
});
