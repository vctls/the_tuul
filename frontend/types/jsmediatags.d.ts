declare interface Window {
    jsmediatags: {
        read(file: File, callbacks: {
            onSuccess(tag: { tags: { artist: string, title: string } }): void,
            onFailure(error: any): void
        }): void
    }
}