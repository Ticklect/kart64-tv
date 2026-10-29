package com.ticklect.kart64;
import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.TextView;
import org.mozilla.geckoview.*;
import fi.iki.elonen.NanoHTTPD;
import java.io.*;
import java.util.*;

public final class GeckoActivity extends Activity {
    private static GeckoRuntime runtime;
    private GeckoSession session;
    private LocalContent server;
    @Override public void onCreate(Bundle state){
        super.onCreate(state);getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        try{
            server=new LocalContent();server.start(NanoHTTPD.SOCKET_READ_TIMEOUT,true);
            GeckoView view=new GeckoView(this);setContentView(view);
            if(runtime==null)runtime=GeckoRuntime.create(getApplicationContext());
            session=new GeckoSession();session.setContentDelegate(new GeckoSession.ContentDelegate(){});
            session.setNavigationDelegate(new GeckoSession.NavigationDelegate(){
                @Override public GeckoResult<AllowOrDeny> onLoadRequest(GeckoSession s,LoadRequest r){return GeckoResult.fromValue(r.uri.startsWith(server.origin()+"/")?AllowOrDeny.ALLOW:AllowOrDeny.DENY);}
            });
            session.open(runtime);view.setSession(session);session.loadUri(server.origin()+"/"+server.token+"/assets/launch.html");view.requestFocus();
        }catch(Exception e){TextView error=new TextView(this);error.setText("Kart64 TV could not start: "+e.getClass().getSimpleName());setContentView(error);}
    }
    @Override protected void onPause(){if(session!=null)session.setActive(false);super.onPause();}
    @Override protected void onResume(){super.onResume();if(session!=null)session.setActive(true);}
    @Override protected void onDestroy(){if(session!=null)session.close();if(server!=null)server.stop();super.onDestroy();}
    private final class LocalContent extends NanoHTTPD{
        final String token=UUID.randomUUID().toString();
        LocalContent(){super("127.0.0.1",18864);}
        String origin(){return "http://127.0.0.1:"+getListeningPort();}
        @Override public Response serve(IHTTPSession request){
            try{
                String path=request.getUri(),prefix="/"+token+"/";
                if(!("127.0.0.1:"+getListeningPort()).equals(request.getHeaders().get("host"))||!path.startsWith(prefix)||path.contains("..")||path.contains("\\"))return deny();
                path=path.substring(prefix.length());
                if(request.getMethod()==Method.POST&&path.equals("report")){
                    int length=Integer.parseInt(request.getHeaders().getOrDefault("content-length","0"));
                    if(length<1||length>4096||!origin().equals(request.getHeaders().get("origin")))return deny();
                    Map<String,String> data=new HashMap<>();request.parseBody(data);String report=data.getOrDefault("postData","");
                    if(report.length()>4096)return deny();Log.i("Kart64TV","KART64_CAPABILITIES "+report);return newFixedLengthResponse("OK");
                }
                if(request.getMethod()!=Method.GET&&request.getMethod()!=Method.HEAD)return deny();
                InputStream body;long size;
                if(path.startsWith("assets/")){ByteArrayOutputStream bytes=new ByteArrayOutputStream();try(InputStream in=getAssets().open(path.substring(7))){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)bytes.write(b,0,n);}byte[] content=bytes.toByteArray();body=new ByteArrayInputStream(content);size=content.length;}
                else if(path.startsWith("game/")){File root=new File(getFilesDir(),"web").getCanonicalFile(),file=new File(root,path.substring(5)).getCanonicalFile();if(!file.toPath().startsWith(root.toPath())||!file.isFile())return missing();body=new FileInputStream(file);size=file.length();}
                else return missing();
                String mime=path.endsWith(".html")?"text/html":path.endsWith(".js")?"application/javascript":path.endsWith(".wasm")?"application/wasm":path.endsWith(".json")?"application/json":path.endsWith(".png")?"image/png":"application/octet-stream";
                Response response=newFixedLengthResponse(Response.Status.OK,mime,body,size);
                response.addHeader("Cross-Origin-Opener-Policy","same-origin");response.addHeader("Cross-Origin-Embedder-Policy","require-corp");response.addHeader("Cross-Origin-Resource-Policy","same-origin");
                response.addHeader("Content-Security-Policy","default-src 'self' blob: data:; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; style-src 'self' 'unsafe-inline'; connect-src 'self'; worker-src 'self' blob:;");return response;
            }catch(FileNotFoundException e){return missing();}catch(Exception e){return deny();}
        }
        Response deny(){return newFixedLengthResponse(Response.Status.FORBIDDEN,"text/plain","Blocked");}
        Response missing(){return newFixedLengthResponse(Response.Status.NOT_FOUND,"text/plain","Not found");}
    }
}
