import Vue from "vue";
import Buefy from 'buefy';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

import { createPinia, PiniaVuePlugin } from "pinia";
import { setupErrorHandling } from "@/lib/util";

import App from "@/App.vue";

import "@/main.scss";

import { library } from '@fortawesome/fontawesome-svg-core';

// Import entire icon packs
import { fas } from '@fortawesome/free-solid-svg-icons';
import { far } from '@fortawesome/free-regular-svg-icons';
import { fab } from '@fortawesome/free-brands-svg-icons';

// Add all icons to library (all three styles)
library.add(fas, far, fab);


Vue.component('font-awesome-icon', FontAwesomeIcon);
Vue.use(Buefy, {
    defaultIconPack: 'fas',
    defaultIconComponent: 'font-awesome-icon',
});
Vue.use(PiniaVuePlugin);

// Set error handling
const logError = setupErrorHandling();
Vue.config.errorHandler = logError;

window.addEventListener('load', function () {
    const pinia = createPinia();
    const main = new Vue({
        pinia,
        el: '#app',
        components: {
            App
        },
        template: '<App/>'
    });
});

export default Vue