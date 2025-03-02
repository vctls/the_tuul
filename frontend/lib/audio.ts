import jszip from "jszip";
import { API_HOSTNAME } from "@/constants";
import { SeparationModel } from "@/types";

// Functions for working with audio files and streams
export interface TrackSeparationResult {
    backing: Blob; // Blob of backing track
    vocals: Blob; // Blob of vocals track
}

export async function separateTrack(songFile: File, modelName: SeparationModel): Promise<TrackSeparationResult> {
    // Separate the track and return a blob of the accompaniment stem data
    const formData = new FormData();
    formData.append("songFile", songFile);
    formData.append("modelName", modelName);
    const url = `${API_HOSTNAME}/separate_track`;
    const response = await fetch(url, {
        method: "POST",
        body: formData,
    });
    const zipContents = await response.blob();
    console.log("Received separated audio. Unzipping...");
    const zip = await jszip.loadAsync(zipContents);
    const accompaniment = await zip.file("accompaniment.wav").async("blob").then((blob) => {
        return new Blob([blob], { type: "audio/wav" });
    });

    const vocals = await zip.file("vocals.wav").async("blob").then((blob) => {
        return new Blob([blob], { type: "audio/wav" });
    });

    return { backing: accompaniment, vocals: vocals };
}

export default { separateTrack }