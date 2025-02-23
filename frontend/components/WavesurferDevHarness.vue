<template>
  <div>
    <timing-adjuster
      :lyrics="lyrics"
      :timings="timings"
      :audioDataUrl="audioDataUrl"
      @input="onTimingsUpdated"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { RegionParams } from "wavesurfer.js/dist/plugins/regions.esm.js";
import { LYRIC_MARKERS } from "@/constants";
import { LyricEvent } from "@/lib/timing";
import { Region } from "@/lib/wavesurferPlugins/OpenEndedRegionPlugin";
import TimingAdjuster from "@/components/TimingAdjuster.vue";

function createLyricRegion(params): RegionParams {
  return {
    loop: false,
    drag: false,
    resize: true,
    ...params,
  };
}

export default defineComponent({
  components: { TimingAdjuster },
  data() {
    const lyrics = ["one", "two", "three", "four"];
    const timings: LyricEvent[] = [
      [1.0, LYRIC_MARKERS.SEGMENT_START],
      [2.0, LYRIC_MARKERS.SEGMENT_END],
      [3.0, LYRIC_MARKERS.SEGMENT_START],
      [4.0, LYRIC_MARKERS.SEGMENT_START],
      [5.0, LYRIC_MARKERS.SEGMENT_END],
      [6.0, LYRIC_MARKERS.SEGMENT_START],
    ];
    return {
      timings,
      lyrics,
      audioDataUrl: "",
      regions: [
        createLyricRegion({
          start: 0.0,
          end: 5.0,
          content: "one",
          color: "rgba(255, 0, 0, 0.5)",
        }),
        createLyricRegion({
          start: 7.0,
          end: 12.0,
          content: "two",
          color: "rgba(0, 255, 0, 0.5)",
        }),
        createLyricRegion({
          start: 14.0,
          end: 19.0,
          content: "three",
          color: "rgba(0, 0, 255, 0.5)",
        }),
      ],
    };
  },
  async mounted() {
    const response = await fetch("/static/spaTreatment.m4a");
    const audioUrl = URL.createObjectURL(await response.blob());
    this.audioDataUrl = audioUrl;
  },
  methods: {
    onTimingsUpdated(newTimings: Array<LyricEvent>) {
      console.log("Timings updated", newTimings);
      this.timings = newTimings;
    },
  },
});
</script>