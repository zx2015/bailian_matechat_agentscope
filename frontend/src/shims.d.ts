/// <reference types="vite/client" />

declare module '@matechat/core' {
  const MateChat: {
    install(app: import('vue').App): void;
  };
  export default MateChat;
}
