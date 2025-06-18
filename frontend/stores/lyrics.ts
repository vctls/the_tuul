import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { parseLyrics } from '@/lib/timing';

export const useLyricsStore = defineStore('lyrics', () => {
  const lyricText = ref('');

  // Parse marked up lyrics into segments using shared logic
  const lyricSegments = computed(() => {
    return parseLyrics(lyricText.value, true);
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
