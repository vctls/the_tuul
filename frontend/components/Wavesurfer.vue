<template>
  <div ref="wavesurfer-container" class="wavesurfer-container"></div>
</template>

<script lang="ts">
// A Vue wrapper for a WaveSurfer instance
import { defineComponent } from "vue";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "@/lib/wavesurferPlugins/OpenEndedRegionPlugin";

export default defineComponent({
  props: {
    audioDataUrl: {
      type: String,
      required: true,
    },
    cursorColor: {
      type: String,
      default: "gray",
    },
    cursorWidth: {
      type: Number,
      default: 1,
    },
    mediaControls: {
      type: Boolean,
      default: false,
    },
    minPxPerSec: {
      type: Number,
      default: 50,
    },
    regions: {
      type: Array,
      default: () => [],
    },
    waveColor: {
      type: String,
      default: "rgba(0, 0, 0, 0.1)",
    },
  },
  data() {
    return {
      wavesurfer: null as WaveSurfer | null,
      regionsPlugin: null as RegionsPlugin | null,
    };
  },
  mounted() {
    this.regionsPlugin = RegionsPlugin.create();

    this.wavesurfer = WaveSurfer.create({
      autoScroll: true,
      container: this.$refs["wavesurfer-container"] as HTMLElement,
      cursorColor: this.cursorColor,
      cursorWidth: this.cursorWidth,
      mediaControls: this.mediaControls,
      waveColor: this.waveColor,
      progressColor: "purple",
      barWidth: 3,
      barHeight: 1,
      barGap: 2,
      height: 100,
      minPxPerSec: this.minPxPerSec,
      //   responsive: true,
      normalize: true,
      plugins: [this.regionsPlugin],
    });
    this.wavesurfer.load(this.audioDataUrl);
    // Add regions after audio is decoded or they won't render right
    this.wavesurfer.on("decode", () => {
      for (const region of this.regions) {
        console.log(region);
        this.regionsPlugin.addRegion(region);
      }
    });
  },
  watch: {
    audioDataUrl(newAudioDataUrl) {
      if (this.wavesurfer) {
        this.wavesurfer.load(newAudioDataUrl);
      }
    },
    regions(newRegions) {
      if (this.wavesurfer) {
        this.regionsPlugin.clearRegions();
        this.$nextTick(() => {
          for (const region of newRegions) {
            this.regionsPlugin.addRegion(region);
          }
        });
      }
    },
  },
  beforeUnmount() {
    if (this.wavesurfer) {
      this.wavesurfer.destroy();
    }
  },
});
</script>