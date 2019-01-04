#include <sys/stat.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>
#include <bits/stdc++.h>
using namespace std;

char FALLBACK_EXECUTABLE[77]="";
const double TIMEOUT=4.85;

inline bool file_exists(const char name[]) {
    struct stat buffer;
    return stat(name,&buffer)==0;
}

inline long long timestamp_us() {
    struct timeval tp;
    gettimeofday(&tp,0);
    return 1000000LL*tp.tv_sec+tp.tv_usec;
}

char session_id[77],inp_fn[77],out_fn[77],fallback_fn[77];

int main() {
    long long start_time=timestamp_us();
    bool SKIP_MCC=file_exists("/data/misaka_offline.txt");

    sprintf(session_id,"%lld",start_time);
    sprintf(inp_fn,"/data/misaka_query_%s.txt",session_id);
    sprintf(out_fn,"/data/misaka_answer_%s.txt",session_id);
    sprintf(fallback_fn,"/tmp/misaka_fallback_%s.txt",session_id);

    FILE *fin=fopen(inp_fn,"w");
    while(int c=getchar()) {
        if(c==EOF) break;
        fputc(c,fin);
    }
    fclose(fin);

    if(FALLBACK_EXECUTABLE[0]!='\0') {
        if(int fallback_pid=fork()) {
            int status;
            waitpid(fallback_pid,&status,0);
        } else {
            freopen(inp_fn,"r",stdin);
            freopen(fallback_fn,"w",stdout);
            if(execl(FALLBACK_EXECUTABLE,"",NULL))
                printf("mcc fallback execute errno %s\n",strerror(errno));
            return 0;
        }
    }

    if(!SKIP_MCC)
        while(!file_exists(out_fn) && (timestamp_us()-start_time)<TIMEOUT*1000000) {
            usleep(1000*50);
            FILE *fkeepalive=fopen("/data/misaka_keepalive.txt","w");
            fputc('.',fkeepalive);
            fclose(fkeepalive);
            unlink("/data/misaka_keepalive.txt");
        }

    if(file_exists(out_fn)) { // use mcc result
        usleep(1000*50); // fix race condition
        FILE *fout=fopen(out_fn,"r");
        while(int c=fgetc(fout)) {
            if(c==EOF) break;
            putchar(c);
        }
        fclose(fout);
        unlink(out_fn);
        if(file_exists(fallback_fn))
            unlink(fallback_fn);
    } else if(file_exists(fallback_fn)) { // use fallback
        usleep(1000*50); // fix race condition
        FILE *fout=fopen(fallback_fn,"r");
        while(int c=fgetc(fout)) {
            if(c==EOF) break;
            putchar(c);
        }
        fclose(fout);
        unlink(fallback_fn);
    } else {
        puts("mcc error no output");
    }

    unlink(inp_fn);

    return 0;
}
