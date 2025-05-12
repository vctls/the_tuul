<template>
  <div class="wrapper">
    <b-navbar shadow :mobile-burger="false">
      <template #brand>
        <b-navbar-item tag="span">
          <span class="title">The Tüül</span>
        </b-navbar-item>
        <b-navbar-item>
          <span class="subtitle mb-0">
            &nbsp;(For Making Decent Karaoke Videos From Any Song in About 10
            Minutes)</span></b-navbar-item>
      </template>
      <template #end>
        <b-navbar-item>
          <div class="buttons">
            <b-button v-if="DONATE_URL" tag="a" :href="DONATE_URL" type="is-text" target="_blank">
              <b-icon icon="circle-dollar-to-slot" size="is-large" title="Buy Me A Coffee">
              </b-icon></b-button>
            <b-button tag="a" href="https://github.com/incidentist/the_tuul" type="is-text">
              <b-icon pack="fab" icon="github" size="is-large" title="GitHub">
              </b-icon></b-button>
          </div>
        </b-navbar-item>
      </template>
    </b-navbar>
    <b-tabs expanded :vertical="!isMobile" type="is-boxed" class="main-tabs">
      <help-tab></help-tab>
      <song-info-tab v-model="songInfo" @options-change="onOptionsChange"
        :music-separation-model="musicSeparationModel"></song-info-tab>
      <lyric-input-tab v-model="lyricText"></lyric-input-tab>
      <song-timing-tab :song-info="songInfo" :lyric-segments="lyricsStore.lyricSegments"></song-timing-tab>
      <timing-adjustment-tab :lyrics="lyricText" :songInfo="songInfo" />
      <submit-tab :song-info="songInfo" :lyric-text="lyricText" :music-separation-model="musicSeparationModel"
        :enabled="isReadyToSubmit"></submit-tab>
    </b-tabs>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { isMobile } from "@/lib/device";
import { DONATE_URL } from "@/constants";
import HelpTab from "@/components/HelpTab.vue";
import SongInfoTab from "@/components/SongInfoTab.vue";
import LyricInputTab from "@/components/LyricInputTab.vue";
import SongTimingTab from "@/components/SongTimingTab.vue";
import TimingAdjustmentTab from "@/components/TimingAdjustmentTab.vue";
import SubmitTab from "@/components/SubmitTab.vue";
import {
  BACKING_VOCALS_SEPARATOR_MODEL,
  useMediaStore,
} from "@/stores/media";
import { useLyricsStore } from "@/stores/lyrics";
import { useTimingsStore } from "@/stores/timings";
// import mountedHarness from "@/mountedHarness";
import { LyricEvent } from "./lib/timing";
import { storeToRefs } from "pinia";

export default defineComponent({
  // mixins: [mountedHarness],
  components: {
    HelpTab,
    SongInfoTab,
    LyricInputTab,
    SongTimingTab,
    TimingAdjustmentTab,
    SubmitTab,
  },
  setup() {
    const mediaStore = useMediaStore();
    const lyricsStore = useLyricsStore();
    const timingsStore = useTimingsStore();

    const { lyricText } = storeToRefs(lyricsStore);

    return {
      mediaStore,
      lyricsStore,
      timingsStore,
      lyricText,
    };
  },
  data() {
    return {
      DONATE_URL,
      // Object containing song info: file, artist, title
      songInfo: {
        file: null,
        artist: null,
        title: null,
        duration: null,
        youtubeUrl: null,
        videoBlob: null,
      },
      musicSeparationModel: BACKING_VOCALS_SEPARATOR_MODEL,
      isSubmitting: false,
    };
  },

  computed: {
    isReadyToSubmit() {
      return (
        this.songInfo &&
        this.songInfo.file &&
        this.lyricText.length > 0 &&
        this.timingsStore.areTimingsFinished
      );
    },
    isMobile,
  },
  methods: {
    onOptionsChange(newOptions) {
      for (const key in newOptions) {
        if (key == "backingTrack") {
          this.mediaStore.setBackingTrack(newOptions[key]);
        } else if (Object.hasOwnProperty.call(newOptions, key)) {
          const newValue = newOptions[key];
          this[key] = newValue;
        }
      }
    },

  },
});
</script>

<style scoped>
.main-tabs {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  overflow: hidden;
}

.b-tabs.is-vertical {
  flex-wrap: nowrap;
}

.scroll-wrapper {
  overflow-y: scroll;
  -webkit-overflow-scrolling: touch;
  height: 100%;
}
</style>
<style>
.b-tabs.main-tabs .tab-content {
  flex-grow: 1;
  overflow: hidden;
}
</style>
