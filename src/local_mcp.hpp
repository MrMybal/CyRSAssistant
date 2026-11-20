#pragma once
// Local MCP settings are independent of the assistant permission mode.
struct LocalMcp {
    bool enabled = false;
    int profile = 0; // Free, Local controlled, Token only, Protected.
    uint64_t epoch = 1;
    std::string capability, token, url, phase = "disabled", message;
    static std::string secret() {
        static constexpr char digits[]="0123456789abcdef";
        std::random_device random;std::string value;
        for(int n=0;n<8;++n){auto word=random();for(int i=0;i<8;++i){value+=digits[word&15];word>>=4;}}
        return value;
    }
    bool controlled() const { return profile==1 || profile==3; }
    bool require_token() const { return profile==2 || profile==3; }
    void restart() {++epoch;capability=secret();token=require_token()?secret():"";url.clear();phase=enabled?"starting":"disabled";message.clear();}
    json snapshot() const {return {{"enabled",enabled},{"profile",profile},{"epoch",epoch},{"url",url},{"phase",phase},{"message",message},{"requires_token",require_token()}};}
};
