#include <sys/stat.h>
#include <unistd.h>
#include <bits/stdc++.h>
using namespace std;

inline bool file_exists(char name[]) {
    struct stat buffer;
    return stat(name,&buffer)==0;
}

char session_id[77],inp_fn[77],out_fn[77];
int main() {
    sprintf(session_id,"%d%06d",(int)time(0),int(1000000.*rand()/RAND_MAX));
    sprintf(inp_fn,"/data/misaka_query_%s.txt",session_id);
    sprintf(out_fn,"/data/misaka_answer_%s.txt",session_id);
    
    FILE *fin=fopen(inp_fn,"w");
    while(int c=getchar()) {
        if(c==EOF) break;
        fputc(c,fin);
    }
    fclose(fin);
    
    while(!file_exists(out_fn)) {
        usleep(1000*50);
        
        FILE *fkeepalive=fopen("/data/misaka_keepalive.txt","w");
        fputc('.',fkeepalive);
        fclose(fkeepalive);
        
        unlink("/data/misaka_keepalive.txt");
    }
    
    FILE *fout=fopen(out_fn,"r");
    while(int c=fgetc(fout)) {
        if(c==EOF) break;
        putchar(c);
    }
    fclose(fout);
    
    unlink(inp_fn);
    unlink(out_fn);
    return 0;
}