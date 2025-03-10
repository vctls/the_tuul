import { shallowMount } from '@vue/test-utils';
const { createCanvas, ImageData } = require('canvas');
import SubtitleDisplay from './SubtitleDisplay.vue';

beforeAll(() => {
    // Mock ImageData with TypeScript types
    global.ImageData = ImageData;

    // Mock postMessage
    global.postMessage = jest.fn();

    // Mock Worker
    global.Worker = class {
        postMessage: jest.Mock;
        addEventListener: jest.Mock;
        removeEventListener: jest.Mock;
        terminate: jest.Mock;

        constructor() {
            this.postMessage = jest.fn();
            this.addEventListener = jest.fn();
            this.removeEventListener = jest.fn();
            this.terminate = jest.fn();
        }
    } as unknown as typeof Worker;
});

describe('SubtitleDisplay', () => {
    it('renders', () => {
        const wrapper = shallowMount(SubtitleDisplay, {
            propsData: {
                subtitles: '',
                fonts: {}
            }
        });
        expect(wrapper.find('canvas.subtitle-canvas').exists()).toBe(true);
    });
});