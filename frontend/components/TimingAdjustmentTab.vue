<template>
  <b-tab-item icon="flask" label="Adjust (BETA)" :disabled="!isEnabled" class="timing-adjustment-tab"
    headerClass="timing-adjustment-tab-header">
    <div class="content">
      <p>
        Use this tab to adjust lyric timings by dragging the start of the
        lyric's rectangle. If you marked the end of a lyric with the Enter key,
        you can also adjust the end of it.
      </p>
    </div>
    <subtitle-display class="subtitle-display" v-if="songFile && subtitles" ref="subtitleDisplay" :subtitles="subtitles"
      :fonts="{}" />
    <timing-adjuster v-if="songFile && subtitles" ref="timing-adjuster" :lyrics="lyricText"
      :timings="timingsStore.rawTimings" :audioData="songFile" :vocalTrack="vocalTrack" @timingschange="onTimingsChange"
      @timeupdate="onPlayheadUpdate" @seeking="onPlayheadUpdate" />
  </b-tab-item>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import {
  createAssFile,
  LyricEvent,
  DEFAULT_KARAOKE_OPTIONS,
} from "@/lib/timing";
import TimingAdjuster from "@/components/TimingAdjuster.vue";
import SubtitleDisplay from "./SubtitleDisplay.vue";
import { useMediaStore } from "@/stores/media";
import { useTimingsStore } from "@/stores/timings";
import { useLyricsStore } from "@/stores/lyrics";
import { storeToRefs } from "pinia";

export default defineComponent({
  components: { TimingAdjuster, SubtitleDisplay },
  setup() {
    const mediaStore = useMediaStore();
    const timingsStore = useTimingsStore();
    const lyricsStore = useLyricsStore();
    const { lyricText } = storeToRefs(lyricsStore);
    return {
      mediaStore,
      timingsStore,
      lyricText,
    };
  },
  data() {
    return {
      // Controls playhead in video and adjuster (in seconds)
      playhead: 0.0,
    };
  },
  computed: {
    songFile(): Blob | null {
      return this.mediaStore.songFile;
    },
    vocalTrack(): Blob | null {
      return this.mediaStore.separatedTrack?.vocals || null;
    },
    isEnabled(): boolean {
      return this.timingsStore.length > 0;
    },
    subtitles() {
      try {
        if (this.timingsStore.length === 0) {
          return "";
        }
        return createAssFile(
          this.lyricText,
          this.timingsStore.rawTimings,
          this.mediaStore.songDuration,
          "",
          "",
          {
            ...DEFAULT_KARAOKE_OPTIONS,
            addTitleScreen: false,
            addCountIns: false,
          }
        );
      } catch (e) {
        console.error("Failed to create subtitles", e);
        return "";
      }
    },
  },
  watch: {
    playhead(newPlayhead: number) {
      if (this.$refs.subtitleDisplay) {
        this.$refs.subtitleDisplay.setPlayhead(newPlayhead);
      }
    },
  },
  methods: {
    onTimingsChange(newTimings: Array<LyricEvent>) {
      this.timingsStore.resetTimings(newTimings);
    },
    onPlayheadUpdate(newPlayhead: number) {
      if (newPlayhead !== this.playhead) {
        this.playhead = newPlayhead;
      }
    },
  },
});
</script>

<style scoped>
.timing-adjustment-tab {
  display: flex;
  flex-direction: column;
}

.subtitle-display {
  align-self: center;
}
</style>
