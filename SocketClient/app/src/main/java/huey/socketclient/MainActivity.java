package huey.socketclient;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.pm.PackageManager;

import android.os.StrictMode;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.InputStreamReader;

import java.io.IOException;
import java.net.UnknownHostException;

public class MainActivity extends AppCompatActivity
{
    //TODO Make list of file clickable and add to download input box

    private final String IP_PERSIST_FILE = "Ip_Persist";

    private final int REQUESTCODE = 100;

    private boolean CAN_WRITE_EXTERNAL_STORAGE  = false,
                    CAN_READ_EXTERNAL_STORAGE   = false,
                    CAN_ACCESS_WIFI_STATE       = false,
                    CAN_INTERNET                = false,
                    CAN_ACCESS_NETWORK_STATE    = false;

    private TextView fileView;
    private TextView downloadBar;

    private EditText serverIp;
    private EditText fileInput;

    private Button connectBtn;
    private Button disconnectBtn;
    private Button downloadBtn;
    private Button fileListBtn;
    private Button helpBtn;

    private SocketClient client;

    @Override
    protected void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        StrictMode.ThreadPolicy policy = new StrictMode.ThreadPolicy.Builder().permitAll().build();
        StrictMode.setThreadPolicy(policy);

        // Request permissions to read/write to storage, access wifi state, internet, network state
        requestPermission(this);

        try
        {
            client = new SocketClient(this);
        }
        catch (UnknownHostException e)
        {
        }

        fileView  = (TextView) findViewById(R.id.fileView);
        downloadBar = (TextView) findViewById(R.id.progressBar);

        connectBtn = (Button) findViewById(R.id.connect);
        disconnectBtn = (Button) findViewById(R.id.disconnect);
        downloadBtn = (Button) findViewById(R.id.download);
        fileListBtn = (Button) findViewById(R.id.fileList);

        serverIp = (EditText) findViewById(R.id.serverIp);
        fileInput = (EditText) findViewById(R.id.fileInput);

        fileView.setHorizontallyScrolling(true);
        fileView.setMovementMethod(new ScrollingMovementMethod());

        String prevIp = getPrevIp();
        if (prevIp != null)
            serverIp.setText(prevIp);

        connectBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                try
                {
                    String ip = serverIp.getText().toString();
                    saveIp(ip);
                    client.connect(ip);
                }
                catch (IOException e)
                {
                    e.printStackTrace();
                }
            }
        });

        disconnectBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                try
                {
                    client.disconnect();
                }
                catch (IOException e)
                {
                    e.printStackTrace();
                }
            }
        });

        downloadBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                try
                {
                    int fileNo = Integer.parseInt(fileInput.getText().toString());
                    client.download(fileNo);
                }
                catch (NumberFormatException e)
                {
                    String input = fileInput.getText().toString();
                    if (input.toLowerCase().equals("all"))
                        client.downloadAll();

                }
            }
        });

        fileListBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                String list = client.getFileList();
                if (list != null)
                {
                    list = list.replaceAll(" ", "  "); // Android messes up white space, need to double
                    fileView.setText(list);
                }
            }
        });
    }

    private boolean requestPermission(Activity activity)
    {
        int pReadExternalStorage    = ActivityCompat.checkSelfPermission(activity, Manifest.permission.READ_EXTERNAL_STORAGE),
            pWriteExternalStorage   = ActivityCompat.checkSelfPermission(activity, Manifest.permission.WRITE_EXTERNAL_STORAGE),
            pAccessWifiState        = ActivityCompat.checkSelfPermission(activity, Manifest.permission.ACCESS_WIFI_STATE),
            pInternet               = ActivityCompat.checkSelfPermission(activity, Manifest.permission.INTERNET),
            pAccessNetworkState     = ActivityCompat.checkSelfPermission(activity, Manifest.permission.ACCESS_NETWORK_STATE);

        if (pReadExternalStorage        == PackageManager.PERMISSION_GRANTED
            && pWriteExternalStorage    == PackageManager.PERMISSION_GRANTED
            && pAccessWifiState         == PackageManager.PERMISSION_GRANTED
            && pInternet                == PackageManager.PERMISSION_GRANTED
            && pAccessNetworkState      == PackageManager.PERMISSION_GRANTED)
        {
            CAN_WRITE_EXTERNAL_STORAGE  = true;
            CAN_READ_EXTERNAL_STORAGE   = true;
            CAN_ACCESS_WIFI_STATE       = true;
            CAN_INTERNET                = true;
            CAN_ACCESS_NETWORK_STATE    = true;
            return true;
        }

        ActivityCompat.requestPermissions(activity, new String[] {
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE,
            Manifest.permission.ACCESS_WIFI_STATE,
            Manifest.permission.INTERNET,
            Manifest.permission.ACCESS_NETWORK_STATE,
        }, REQUESTCODE);

        return false;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode,
                                           String permissions[],
                                           int[] grantResults)
    {
        switch (requestCode)
        {
            case REQUESTCODE:
            {
                // If request is cancelled, the result arrays are empty.
                if (grantResults.length > 0
                    && grantResults[0] == PackageManager.PERMISSION_GRANTED)
                {
                    CAN_WRITE_EXTERNAL_STORAGE      = true;
                    CAN_READ_EXTERNAL_STORAGE       = true;
                    CAN_ACCESS_WIFI_STATE           = true;
                    CAN_INTERNET                    = true;
                    CAN_ACCESS_NETWORK_STATE        = true;
                }
                else
                {
                    CAN_WRITE_EXTERNAL_STORAGE      = false;
                    CAN_READ_EXTERNAL_STORAGE       = false;
                    CAN_ACCESS_WIFI_STATE           = false;
                    CAN_INTERNET                    = false;
                    CAN_ACCESS_NETWORK_STATE        = false;
                }
                break;
            }
            default: return;
        }
    }

    private void saveIp(String ip)
    {
        if (CAN_READ_EXTERNAL_STORAGE && CAN_WRITE_EXTERNAL_STORAGE)
        {
             try
             {
                 FileOutputStream out = openFileOutput(IP_PERSIST_FILE, Context.MODE_PRIVATE);
                 out.write(ip.getBytes());
                 out.close();
             }
             catch (FileNotFoundException e)
             {
                 e.printStackTrace();
             }
             catch (IOException e)
             {
                 e.printStackTrace();
             }
        }
    }

    private String getPrevIp()
    {
        File file = new File(this.getFilesDir(), IP_PERSIST_FILE);
        if (!file.exists())
            return null;
        else
        {
            try
            {
                BufferedReader br = new BufferedReader(new InputStreamReader(openFileInput(IP_PERSIST_FILE)));
                String line;
                while ((line = br.readLine()) != null)
                {
                    return line; // First line of file should just be the persist ip
                }
            }
            catch (FileNotFoundException e)
            {
                e.printStackTrace();
            }
            catch (IOException e)
            {
                e.printStackTrace();
            }
        }
        return null;
    }

    protected void alert(String title, String msg)
    {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);

        builder.setMessage(msg)
                .setTitle(title != null ? title : "Message");

        AlertDialog dialog = builder.create();
        dialog.show();
    }
}
