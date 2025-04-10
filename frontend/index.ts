import Vue from "vue";
import Buefy from 'buefy';
import { createPinia, PiniaVuePlugin } from "pinia";
import { setupErrorHandling } from "@/lib/util";
import App from "@/App.vue";
import "@/main.scss";

// Import our optimized FontAwesome configuration
import './plugins/fontawesome';

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