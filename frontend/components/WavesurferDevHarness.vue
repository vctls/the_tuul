<template>
  <div>
    <wavesurfer
      :audioDataUrl="audioDataUrl"
      :regions="regions"
      :mediaControls="true"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import Wavesurfer from "@/components/Wavesurfer.vue";
import { RegionParams } from "wavesurfer.js/dist/plugins/regions.esm.js";

function createLyricRegion(params): RegionParams {
  return {
    loop: false,
    drag: false,
    resize: true,
    ...params,
  };
}

export default defineComponent({
  components: { Wavesurfer },
  data() {
    return {
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
});
</script>