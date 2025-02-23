<template>
  <div>
    <wavesurfer
      ref="wavesurfer"
      :audioDataUrl="audioDataUrl"
      :regions="regions"
      :mediaControls="true"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { RegionParams } from "@/lib/wavesurferPlugins/OpenEndedRegionPlugin";
import Wavesurfer from "@/components/Wavesurfer.vue";

import { LyricEvent } from "@/lib/timing";
import { LYRIC_MARKERS } from "@/constants";

function createLyricRegion(params): RegionParams {
  return {
    loop: false,
    drag: false,
    resize: true,
    ...params,
  };
}

export default defineComponent({
  components: {
    Wavesurfer,
  },
  props: {
    lyrics: Array<String>,
    timings: Array<LyricEvent>,
    audioDataUrl: String,
  },
  data() {
    return {
      regions: [],
    };
  },
  mounted() {
    this.regions = this.createRegions(this.timings, this.lyrics);
  },
  methods: {
    createRegions(
      timings: Array<LyricEvent>,
      lyrics: Array<String>
    ): Array<RegionParams> {
      let regions = [];
      let currentRegion = null;
      let currentLyricIndex = 0;
      for (let i = 0; i < timings.length; i++) {
        const [time, marker] = timings[i];
        if (marker === LYRIC_MARKERS.SEGMENT_START) {
          if (currentRegion) {
            regions.push(currentRegion);
            currentLyricIndex += 1;
          }
          const lyricSegment = lyrics[currentLyricIndex];
          currentRegion = createLyricRegion({
            start: time,
            end: null,
            content: lyricSegment,
            color: "rgba(0, 0, 0, 0.5)",
          });
        } else if (marker === LYRIC_MARKERS.SEGMENT_END) {
          currentRegion.end = time;
        }
      }
      if (currentRegion) {
        regions.push(currentRegion);
      }
      console.log(regions);
      return regions;
    },
  },
});
</script>