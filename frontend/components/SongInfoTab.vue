<template>
  <b-tab-item :class="['help-tab', 'scroll-wrapper']" headerClass="song-info-tab-header">
    <template #header>
      <b-icon v-if="!isSeparatingTrack" icon="file-audio"></b-icon>
      <b-tooltip v-else label="Separating track" position="is-bottom"><span class="icon is-small loader"></span>
      </b-tooltip>
      <span> Song File</span>
    </template>
    <div class="container">
      <h2 class="title">Get Your Song Ready</h2>
      <file-upload name="song-file-upload" label="Upload a file from your computer:" v-model="songFile"
        @update:modelValue="onSongFileChange"></file-upload>
      <b-field label="Or paste a YouTube video URL:" :type="youtubeError ? 'is-danger' : ''">
        <template #message>
          <span v-html="youtubeError"></span>
        </template>
        <b-input type="text" v-model="youtubeUrl" />
        <b-button label="Load" :type="youtubeUrl ? 'is-primary' : 'is-light'" :disabled="!youtubeUrl"
          @click="loadYouTubeUrl" :loading="isLoadingYouTube" />
      </b-field>
      <b-field label="Song Artist">
        <b-input name="artist" v-model="artist" @input="onTextChange" />
      </b-field>
      <b-field label="Song Title">
        <b-input name="title" v-model="title" @input="onTextChange" />
      </b-field>
      <b-field horizontal label="Include Backing Vocals" class="backing-vocals-toggle">
        <b-switch v-model="includeBackingVocals"></b-switch></b-field>
    </div>

    <b-collapse :open="false">
      <template #trigger="props">
        <b-button type="is-text" aria-controls="contentIdForA11y4" :aria-expanded="props.open">
          <span>Advanced</span>
          <b-icon :icon="props.open ? 'angle-down' : 'angle-right'"></b-icon>
        </b-button>
      </template>
      <div class="box">
        <file-upload name="timings-file-upload" :accept="['.json']" label="Timings File" v-model="timingsFile"
          @update:modelValue="onTimingsFileChange" />
        <file-upload label="Backing Track" v-model="backingTrackFile" @update:modelValue="onBackingTrackFileChange" />
      </div>
    </b-collapse>
    <div class="buttons" v-if="!backingTrackFile">
      <b-tooltip position="is-right" :label="separatingTrackMessage" :always="isSeparatingTrack">
        <b-button label="Separate Track" type="is-primary" :disabled="!songFile" :loading="isSeparatingTrack"
          @click="separateTrack" />
      </b-tooltip>
    </div>
  </b-tab-item>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { mapStores } from "pinia";
import { fetchYouTubeVideo, parseYouTubeTitle } from "@/lib/video";
import jsmediatags from "@/jsmediatags.min.js";

import {
  useMediaStore,
  BACKING_VOCALS_SEPARATOR_MODEL,
  NO_VOCALS_SEPARATOR_MODEL,
} from "@/stores/media";
import { useTimingsStore } from "@/stores/timings";
import FileUpload from "@/components/FileUpload.vue";

export default defineComponent({
  components: {
    FileUpload,
  },
  setup() {
    const mediaStore = useMediaStore();
    const timingsStore = useTimingsStore();
    return {
      mediaStore,
      timingsStore,
    };
  },
  props: {
    modelValue: Object,
    musicSeparationModel: {
      type: String,
      default: BACKING_VOCALS_SEPARATOR_MODEL,
    },
  },
  data() {
    return {
      songFile: this.modelValue?.file || null,
      youtubeUrl: this.modelValue?.youtubeUrl || null,
      artist: this.modelValue?.artist || null,
      title: this.modelValue?.title || null,
      duration: this.modelValue?.duration || null,
      isLoadingYouTube: false,
      videoBlob: null,
      timingsFile: null,
      backingTrackFile: null,
      youtubeError: null,
    };
  },
  computed: {
    songInfo() {
      return {
        file: this.songFile,
        artist: this.artist,
        title: this.title,
        duration: this.duration,
        youtubeUrl: this.youtubeUrl,
        videoBlob: this.videoBlob,
      };
    },
    isSeparatingTrack() {
      return this.mediaStore.isProcessing;
    },
    separatingTrackMessage() {
      if (this.isSeparatingTrack) {
        return "Separating track...head to the Lyrics tab to keep working on the song!";
      }
      return "Start separating the track while you work on the song timings. It's faster!";
    },
    includeBackingVocals: {
      get() {
        return this.musicSeparationModel == BACKING_VOCALS_SEPARATOR_MODEL;
      },
      set(value) {
        this.onChange(
          "musicSeparationModel",
          value ? BACKING_VOCALS_SEPARATOR_MODEL : NO_VOCALS_SEPARATOR_MODEL
        );
      },
    },
    ...mapStores(useMediaStore),
  },
  methods: {
    async songDuration(songFile: File): Promise<number> {
      return new Promise<number>((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = async (event) => {
          try {
            const audioContext = new AudioContext();
            const arrayBuffer = event.target.result as ArrayBuffer;

            audioContext.decodeAudioData(
              arrayBuffer,
              (audioBuffer) => {
                const duration = audioBuffer.duration;
                resolve(duration);
              },
              (error) => {
                console.error("Error decoding audio data:", error);
                reject(
                  new Error(
                    "Failed to decode audio data: " +
                    (error?.message || "Unknown error")
                  )
                );
              }
            );
          } catch (error) {
            console.error("Audio context error:", error);
            reject(
              new Error(
                "Failed to create or use AudioContext: " +
                (error?.message || "Unknown error")
              )
            );
          }
        };

        reader.onerror = (event) => {
          console.error("FileReader error:", reader.error);
          reject(
            new Error(
              "Failed to read audio file: " +
              (reader.error?.message || "Unknown error")
            )
          );
        };

        reader.readAsArrayBuffer(songFile);
      });
    },
    onSongFileChange(file: File | null) {
      if (!file) {
        this.songFile = null;
        this.mediaStore.songFile = null;
        this.$emit("update:modelValue", this.songInfo);
        return;
      }
      this.mediaStore.songFile = file;
      const self = this;
      jsmediatags.read(this.songFile, {
        async onSuccess(tag) {
          self.artist = tag.tags.artist;
          self.title = tag.tags.title;
          self.duration = await self.songDuration(self.songFile);
          self.$emit("update:modelValue", self.songInfo);
        },
        onFailure(error) {
          console.error(error);
          self.$emit("update:modelValue", self.songInfo);
        },
      });
    },
    onTextChange(e) {
      this.$emit("update:modelValue", this.songInfo);
    },
    async loadYouTubeUrl() {
      this.isLoadingYouTube = true;
      this.youtubeError = null;
      try {
        const [audioBlob, videoBlob, metadata] = await fetchYouTubeVideo(
          this.youtubeUrl
        );
        this.songFile = new File([audioBlob], "audio.mp4", {
          type: "audio/mp4",
        });
        const parsedMetadata = parseYouTubeTitle(metadata);
        this.artist = parsedMetadata[0];
        this.title = parsedMetadata[1];
        this.duration = await this.songDuration(this.songFile);
        this.videoBlob = videoBlob;

        // Update the media store
        this.mediaStore.songFile = this.songFile;
        this.mediaStore.backgroundVideo = videoBlob;
      } catch (e) {
        console.error(e);
        this.youtubeError = `There was a problem downloading that video: ${e.message}. Please try again or use a service such as <a href="https://v2.youconvert.net/en/">YouConvert</a> to get the audio and add it above.`;
      }
      this.isLoadingYouTube = false;
      this.$emit("update:modelValue", this.songInfo);
    },
    onTimingsFileChange(file: File | null) {
      if (!file) {
        this.timingsStore.resetTimings([]);
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        const timings = JSON.parse(e.target.result.toString());
        this.timingsStore.resetTimings(timings);
      };
      reader.readAsText(file);
    },
    onSeparationModelChange(model) {
      this.onChange("separationModel", model);
    },
    onBackingTrackFileChange(file: File | null) {
      this.mediaStore.setBackingTrack(file);
    },
    onChange(optionName: string, newValue: any) {
      this.$emit("options-change", { [optionName]: newValue });
    },
    async separateTrack() {
      const model = this.musicSeparationModel;
      this.mediaStore.startSeparation(this.songFile, model);

      // Also store the song file and background video in the media store
      this.mediaStore.songFile = this.songFile;
      if (this.videoBlob) {
        this.mediaStore.backgroundVideo = this.videoBlob;
      }
    },
  },
});
</script>
<style scoped>
.song-info-tab {
  overflow-x: hidden;
  overflow-y: auto;
}

.backing-vocals-toggle :deep(.field-label) {
  text-align: left !important;
  flex-grow: 0 !important;
  flex-basis: fit-content;
}
</style>
