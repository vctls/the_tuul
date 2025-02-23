<template>
  <div>
    <wavesurfer
      ref="wavesurfer"
      :audioData="audioData"
      :regions="regions"
      :mediaControls="true"
      @region-updated="onRegionUpdated"
      @timeupdate="onTimeUpdate"
      @seeking="onSeeking"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { LyricSegmentIterator } from "@/lib/timing";
import {
  RegionParams,
  Region,
} from "@/lib/wavesurferPlugins/OpenEndedRegionPlugin";
import Wavesurfer from "@/components/Wavesurfer.vue";

import { LyricEvent, adjustSegmentTiming } from "@/lib/timing";
import { LYRIC_MARKERS } from "@/constants";

function createLyricRegion(id: number, params): RegionParams {
  return {
    id: `segment_${id}`,
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
    lyrics: String,
    timings: Array<LyricEvent>,
    audioData: Blob,
  },
  data() {
    return {
      regions: [],
    };
  },
  computed: {
    splitLyrics(): Array<String> {
      if (this.lyrics == null) {
        return [];
      }
      const lyricIterator = new LyricSegmentIterator(this.lyrics)[
        Symbol.iterator
      ]();

      return [...lyricIterator].map((segment) => segment.text);
    },
  },
  mounted() {
    this.regions = this.createRegions(this.timings, this.splitLyrics);
  },
  watch: {
    timings(newTimings: Array<LyricEvent>) {
      this.regions = this.createRegions(newTimings, this.splitLyrics);
    },
    lyrics(newLyrics: String) {
      this.regions = this.createRegions(this.timings, this.splitLyrics);
    },
  },
  methods: {
    createRegions(
      timings: Array<LyricEvent>,
      lyrics: Array<String>
    ): Array<RegionParams> {
      if (!timings || !lyrics) {
        return [];
      }
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
          currentRegion = createLyricRegion(regions.length, {
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
    onRegionUpdated(region: Region) {
      console.log("TimingAdjuster: Region updated", region.id, region);
      const newTimings = this.applyRegionUpdateToTimings(region, this.timings);
      this.$emit("input", newTimings);
      this.$nextTick(() => {
        this.previewNewTiming(region);
      });
    },
    applyRegionUpdateToTimings(
      region: Region,
      timings: Array<LyricEvent>
    ): Array<LyricEvent> {
      const segmentNum = parseInt(region.id.split("_")[1]);
      return adjustSegmentTiming(segmentNum, timings, {
        start: region.start,
        end: region.end,
      });
    },
    previewNewTiming(region: Region) {
      // When a timing changes, set the playhead 5 seconds before the changed region
      const newPlayhead = Math.max(0, region.start - 5);
      this.setPlayhead(newPlayhead);
    },
    onTimeUpdate(time: number) {
      this.$emit("timeupdate", time);
    },
    onSeeking(time: number) {
      this.$emit("seeking", time);
    },
    setPlayhead(playhead: number) {
      if (playhead != this.$refs.wavesurfer.getCurrentTime()) {
        this.$refs.wavesurfer.setTime(playhead);
      }
    },
  },
});
</script>