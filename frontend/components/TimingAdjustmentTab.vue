<template>
  <b-tab-item
    icon="flask"
    label="Adjust (BETA)"
    :disabled="!enabled"
    class="timing-adjustment-tab"
  >
    <div class="content">
      <p>
        Use this tab to adjust lyric timings by dragging the start of the
        lyric's rectangle. If you marked the end of a lyric with the Enter key,
        you can also adjust the end of it.
      </p>
    </div>
    <subtitle-display
      class="subtitle-display"
      v-if="songFile"
      ref="subtitleDisplay"
      :subtitles="subtitles"
      :fonts="{}"
    />
    <timing-adjuster
      v-if="songFile"
      ref="timing-adjuster"
      :lyrics="lyrics"
      :timings="timings"
      :audioData="musicSeparationStore.audioData"
      @input="onTimingsChange"
      @timeupdate="onPlayheadUpdate"
      @seeking="onPlayheadUpdate"
    />
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
import { useMusicSeparationStore } from "@/stores/musicSeparation";

export default defineComponent({
  components: { TimingAdjuster, SubtitleDisplay },
  props: {
    lyrics: String,
    timings: Array,
    songFile: { type: Blob, required: false },
  },
  setup() {
    const musicSeparationStore = useMusicSeparationStore();
    return {
      musicSeparationStore,
    };
  },
  data() {
    return {
      // Controls playhead in video and adjuster (in seconds)
      playhead: 0.0,
    };
  },
  computed: {
    subtitles() {
      return createAssFile(
        this.lyrics,
        this.timings,
        this.songFile.duration,
        "",
        "",
        {
          ...DEFAULT_KARAOKE_OPTIONS,
          addTitleScreen: false,
          addCountIns: false,
        }
      );
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
      this.$emit("input", newTimings);
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