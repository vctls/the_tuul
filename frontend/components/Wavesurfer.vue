<template>
  <div ref="wavesurfer-container" class="wavesurfer-container"></div>
</template>

<script lang="ts">
// A Vue wrapper for a WaveSurfer instance
import { defineComponent } from "vue";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin, {
  Region,
  RegionsPluginEvents,
} from "@/lib/wavesurferPlugins/OpenEndedRegionPlugin";

export default defineComponent({
  props: {
    audioData: {
      type: Blob,
      required: false,
    },
    cursorColor: {
      type: String,
      default: "pink",
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
    this.wavesurfer.loadBlob(this.audioData);

    this.wavesurfer.on("seeking", (time: number) => {
      this.$emit("seeking", time);
    });

    this.wavesurfer.on("click", (x: number, y: number) => {
      const newX = x * this.wavesurfer.getDuration();
      this.$emit("click", newX, y);
    });

    this.wavesurfer.on("timeupdate", (time: number) => {
      this.$emit("timeupdate", time);
    });

    this.regionsPlugin.on("region-updated", (region: Region) => {
      this.$emit("region-updated", region);
    });

    // // Add regions after audio is decoded or they won't render right
    // this.wavesurfer.on("decode", () => {
    //   for (const region of this.regions) {
    //     console.log(region);
    //     this.regionsPlugin.addRegion(region);
    //   }
    // });
  },
  watch: {
    audioData(newAudioData: Blob) {
      if (this.wavesurfer) {
        this.wavesurfer.loadBlob(newAudioData);
      }
    },
    regions(newRegions) {
      console.log("regions changed", newRegions);
      // // Add regions after audio is decoded or they won't render right
      this.wavesurfer.on("decode", () => {
        for (const region of this.regions) {
          console.log(region);
          this.regionsPlugin.addRegion(region);
        }
      });
      // if (this.wavesurfer) {
      //   this.regionsPlugin.clearRegions();
      //   this.$nextTick(() => {
      //     for (const region of newRegions) {
      //       this.regionsPlugin.addRegion(region);
      //     }
      //   });
      // }
    },
  },
  methods: {
    play() {
      if (this.wavesurfer) {
        this.wavesurfer.play();
      }
    },
    pause() {
      if (this.wavesurfer) {
        this.wavesurfer.pause();
      }
    },
    setTime(time: number) {
      if (this.wavesurfer) {
        this.wavesurfer.setTime(time);
      }
    },
    getCurrentTime() {
      if (this.wavesurfer) {
        return this.wavesurfer.getCurrentTime();
      }
      return 0;
    },
  },
  beforeUnmount() {
    if (this.wavesurfer) {
      this.wavesurfer.destroy();
    }
  },
});
</script>