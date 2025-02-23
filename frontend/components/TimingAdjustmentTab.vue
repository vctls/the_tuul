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
    <timing-adjuster
      v-if="songFile"
      :lyrics="lyrics"
      :timings="timings"
      :audioData="songFile"
      @input="onTimingsChange"
    />
  </b-tab-item>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { LyricEvent } from "@/lib/timing";
import TimingAdjuster from "@/components/TimingAdjuster.vue";

export default defineComponent({
  components: { TimingAdjuster },
  props: {
    lyrics: String,
    timings: Array,
    songFile: { type: Blob, required: false },
  },

  methods: {
    onTimingsChange(newTimings: Array<LyricEvent>) {
      this.$emit("input", newTimings);
    },
  },
});
</script>