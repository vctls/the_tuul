import { defineStore } from 'pinia';
import { ref } from 'vue';

import { separateTrack, TrackSeparationResult } from '@/lib/audio';
import { SeparationModel } from '@/types';

export interface SeparatedTrack {
    // Blob URL of the separated backing track
    backing: string;
    // Blob URL of the separated vocals track
    vocals: string;
}

export const BACKING_VOCALS_SEPARATOR_MODEL = "UVR_MDXNET_KARA_2.onnx";
export const NO_VOCALS_SEPARATOR_MODEL = "UVR-MDX-NET-Inst_HQ_3.onnx";

export const useMusicSeparationStore = defineStore('musicSeparation', () => {
    const isProcessing = ref(false);
    const separatedTrack = ref<SeparatedTrack | null>(null);
    const error = ref<string | null>(null);
    const separationStartTime = ref<Date | null>(null);
    var separationPromise: Promise<SeparatedTrack> = null;
    var resolveResult: (string) => void = null;

    async function startSeparation(inputData: any, modelName: SeparationModel): Promise<SeparatedTrack> {
        if (isProcessing.value) {
            return;
        }
        isProcessing.value = true;
        error.value = null;
        separationStartTime.value = new Date();
        try {
            const result = await separateTrack(inputData, modelName);
            separatedTrack.value = result;
            return separatedTrack.value;
        } catch (err) {
            console.error(err);
            error.value = (err as Error).message;
        } finally {
            isProcessing.value = false;
        }
    };

    async function setBackingTrack(file: File) {
        if (separatedTrack.value == null) {
            separatedTrack.value = { backing: URL.createObjectURL(file), vocals: '' };
        } else if (resolveResult) {
            resolveResult(URL.createObjectURL(file));
        } else {
            console.error("Cannot set backing track: separation started but no resolve function found");
        }
    }

    return {
        isProcessing,
        separatedTrack,
        error,
        startSeparation,
        setBackingTrack,
        separationStartTime,
    };
});

// Fake API call to demonstrate functionality
async function fakeMusicSeparationAPI(inputData: any) {
    return new Promise<string>((resolve) => {
        setTimeout(() => {
            resolve('instrumental.wav');
        }, 2000);
    });
}