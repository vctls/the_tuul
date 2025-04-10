<template>
  <div class="preview-container">
    <b-message type="is-info">
      Audio in this preview includes vocals, but the finished video won't.
    </b-message>
    <subtitle-display
      ref="subtitleDisplay"
      :subtitles="subtitles"
      :audioDelay="audioDelay"
      :fonts="fonts"
      :backgroundColor="backgroundColor"
      :videoBlob="videoBlob"
    />
    <smooth-audio-player
      ref="player"
      :src="audioDataUrl"
      controls
      @timeupdate="onAudioTimeUpdate"
      @playing="onAudioPlaying"
      @pause="onAudioPause"
      @seeking="onAudioSeeking"
      @seeked="onAudioSeeked"
      @waiting="onAudioWaiting"
    />
  </div>
</template>

<script lang="ts">
/* A component that displays WebVTT subtitles over a black screen, with an audio file provided as a prop */
// TODO: Incorporate audio delay

import { defineComponent } from "vue";
import bufferToWav from "audiobuffer-to-wav";
import SubtitleDisplay from "./SubtitleDisplay.vue";
import SmoothAudioPlayer from "./SmoothAudioPlayer.vue";

export default defineComponent({
  components: { SubtitleDisplay, SmoothAudioPlayer },
  props: {
    songFile: {
      type: Blob,
      required: true,
    },
    subtitles: {
      type: String,
      required: true,
    },
    audioDelay: {
      type: Number,
      default: 0.0,
    },
    fonts: {
      type: Object,
    },
    backgroundColor: {
      type: String,
      default: "#000000",
    },
    videoBlob: {
      type: Blob,
      required: false,
    },
  },
  data() {
    return {
      audioDataUrl: "",
    };
  },
  mounted() {
    this.updateAudio(this.songFile, this.audioDelay);
  },
  watch: {
    songFile(newSongFile: Blob) {
      this.updateAudio(newSongFile, this.audioDelay);
    },
  },
  methods: {
    setPlayhead(playhead: number) {
      if (playhead != this.$refs.player.currentTime) {
        this.$refs.player.currentTime = playhead;
      }
      this.$refs.subtitleDisplay.setPlayhead(playhead);
    },
    async updateAudio(audioData: Blob, silence: number) {
      const audioWithSilence = await this.prependSilence(audioData, silence);
      this.audioDataUrl = URL.createObjectURL(audioWithSilence);
    },
    async prependSilence(
      audioData: Blob,
      secondsOfSilence: number
    ): Promise<Blob> {
      // Prepend N seconds of silence to the start of the songfile
      if (secondsOfSilence == 0) {
        return audioData;
      }

      // TODO: can we do some of these steps in parallel?
      const audioContext = new AudioContext();
      const arrayBuffer = await audioData.arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      // Create an OfflineAudioContext with the desired duration
      const offlineAudioContext = new OfflineAudioContext({
        numberOfChannels: audioBuffer.numberOfChannels,
        length: audioBuffer.length + secondsOfSilence * audioBuffer.sampleRate,
        sampleRate: audioBuffer.sampleRate,
      });

      // Create a source node from the original audio buffer
      const source = offlineAudioContext.createBufferSource();
      source.buffer = audioBuffer;

      // Connect the source node to the destination node (output)
      source.connect(offlineAudioContext.destination);

      // Start rendering the audio
      source.start();

      // Wait for the audio to finish rendering
      const songBuffer = await offlineAudioContext.startRendering();

      // Create a new AudioBuffer with the desired length
      const songWithSilenceBuffer = audioContext.createBuffer(
        songBuffer.numberOfChannels,
        songBuffer.length + secondsOfSilence * audioBuffer.sampleRate,
        songBuffer.sampleRate
      );

      // Get the channel data from the result buffer
      for (let channel = 0; channel < songBuffer.numberOfChannels; channel++) {
        const resultData = songBuffer.getChannelData(channel);
        const silenceData = songWithSilenceBuffer.getChannelData(channel);

        // Copy the result data to the end of the silence buffer
        silenceData.set(resultData, secondsOfSilence * audioBuffer.sampleRate);
      }

      // Convert the result buffer to a wav
      const wavAudio: ArrayBuffer = bufferToWav(songWithSilenceBuffer);
      const result = new Blob([new DataView(wavAudio)], {
        type: "audio/wav",
      });

      return result;
    },

    onAudioTimeUpdate(e: Event) {
      const currentTime = (e.target as HTMLAudioElement).currentTime;
      this.setPlayhead(currentTime);
      this.$emit("timeupdate", currentTime);
    },
    // These listeners call some internal libass-wasm functions that dramatically
    // improve rendering performance
    onAudioPlaying() {
      this.$refs.subtitleDisplay.play();
      this.$emit("playing");
    },

    onAudioPause() {
      this.$refs.subtitleDisplay.pause();
      this.$emit("pause");
    },
    onAudioSeeking(e: Event) {
      this.$refs.player.removeEventListener(
        "timeupdate",
        this.onAudioTimeUpdate,
        false
      );
      this.$emit("seeking");
    },

    onAudioSeeked(e: Event) {
      this.$refs.player.addEventListener(
        "timeupdate",
        this.onAudioTimeUpdate,
        false
      );

      var currentTime = (e.target as HTMLAudioElement).currentTime;
      this.$refs.subtitleDisplay.setPlayhead(currentTime);

      this.$emit("seeked", currentTime);
    },
    onAudioWaiting() {
      this.$refs.subtitleDisplay.pause();
      this.$emit("waiting");
    },
  },
});
</script>
<style scoped>
.preview-container {
  text-align: center;
  width: 320px;
}
</style>