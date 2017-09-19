package huey.socketclient;

import android.app.Activity;
import android.content.Context;
import android.os.AsyncTask;
import android.os.Environment;
import android.widget.TextView;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;

import java.text.NumberFormat;
import java.util.Locale;

class SocketClient
{

    private final String REQUEST_FILE_COUNT          = "REQUEST_FILE_COUNT";
    private final String REQUEST_FILE_LIST           = "REQUEST_FILE_LIST";
    private final String REQUEST_FILE_NAME           = "REQUEST_FILE_NAME";
    private final String REQUEST_FILE_DOWNLOAD       = "REQUEST_FILE_DOWNLOAD";

    private final String CONNECTION_RECEIVED         = "CONNECTION_RECEIVED";
    private final String CONNECTION_END              = "CONNECTION_END";

    private final int           MAX_BYTES_IN = (1 << 25);   // 2^n
    private final int           PORT = 1234; //TODO Dynamically assign port number change on server end too
    private InetAddress         host;
    private Socket              socket;
    
    private String serverIp;    

    private Context context;

    private boolean downloading;
    private int downloadPt;    
    private long lastDownloadedSize;

    private int currFilesDownloaded, totalFilesToDownload;

    private NumberFormat numFormat;

    protected SocketClient() throws UnknownHostException
    {
        init();
    }

    protected SocketClient(Context context) throws UnknownHostException
    {
        this.context = context;
        init();
    }

    private void init() throws UnknownHostException
    { 
        host = null;
        socket = null;
        
        serverIp = null;

        downloadPt = 0;
        lastDownloadedSize = 0;
        
        downloading = false;

        numFormat = NumberFormat.getNumberInstance(Locale.US);
        
        //host = InetAddress.getLocalHost();
        new FindHostTask().execute();
    }

    private class FindHostTask extends AsyncTask<Void, Void, Void>
    {
        protected Void doInBackground(Void... voids) 
        {
            try
            {
                host = InetAddress.getLocalHost();
            }
            catch (UnknownHostException e)
            {
            }
            return null;
        }
    }

    private class ConnectTask extends AsyncTask<SocketClient, Void, Void>
    {
        protected Void doInBackground(SocketClient... socketClients)
        {
            socketClients[0].connectTask();
            return null;
        }
    }

    private class DownloadTask extends AsyncTask<Integer, Void, Void>
    {
        protected Void doInBackground(Integer... integers)
        {
            while (getDownloading())
                try
                {
                    Thread.sleep(1000);
                }
                catch (InterruptedException e)
                {
                    e.printStackTrace();
                }

            sendMsg(REQUEST_FILE_NAME + " " + integers[0]);

            try
            {
                byte[] serverReply = receive(new DataInputStream(socket.getInputStream()), null);
                String fileName = new String(serverReply);

                File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
                File file = new File(dir.getPath(), fileName);
                if (!file.exists())
                    file.createNewFile();

                sendMsg(REQUEST_FILE_DOWNLOAD + " " + integers[0]);
                receive(new DataInputStream(socket.getInputStream()), file);
            }
            catch (FileNotFoundException e)
            {
                e.printStackTrace();
            }
            catch (IOException e)
            {
                e.printStackTrace();
            }

            return null;
        }
    }

    private byte[] bSize(int size)
    {
        return ByteBuffer.allocate(4).putInt(size).array();
    }

    private byte[] receive(DataInputStream input, File file) throws IOException
    {
        //Find payload size
        byte[] bPayload = new byte[4];
        for (int i = 0; i < 4; ++i)
        {
            try
            {
                bPayload[i] = input.readByte();
            }
            catch (IOException e)
            {
                //Handle exception here
            }
        }
        ByteBuffer bBuffer = ByteBuffer.wrap(bPayload);
        long totalSize = bBuffer.getInt();
        

        //Fill totalBuffer until payload size
        ByteBuffer totalBuffer = null;
        FileOutputStream out = null;
        if (file == null)
            totalBuffer = ByteBuffer.allocate((int)totalSize);
        else 
        {
            setDownloading(true);
            out = new FileOutputStream(file);
        }

        byte[] buffer = new byte[MAX_BYTES_IN];
        long currentSize = 0;
        int currentPt = 0, 
            numBytesIn = 0,
            downloadPt;
        while (currentSize < totalSize && socket != null)
        {
            System.out.println(currentSize + " / " + totalSize + " bytes");
            try
            {
                if (out == null)
                {
                    
                    numBytesIn = input.read(buffer, 0, MAX_BYTES_IN);
                    totalBuffer.put(buffer, 0, numBytesIn);
                    //totalBuffer.put(input.readByte());
                    currentSize = totalBuffer.position();
                }
                else
                {
                    numBytesIn = input.read(buffer, 0, MAX_BYTES_IN);
                    out.write(buffer, 0, numBytesIn);
                    currentSize += numBytesIn;
                }
            } 
            catch (IOException e) 
            {
                //Handle exception here
            }
           
            downloadPt = (int)((double) currentSize/totalSize * 100);
            if (downloadPt > currentPt)
            {
                currentPt = downloadPt;
                setDownloadPt(currentPt);
                
                ((Activity) context).runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        TextView progressBar = (TextView) ((Activity)context).findViewById(R.id.progressBar);
                        progressBar.setText("Downloading..." + getDownloadPt() + "%");
                    }
                });
                System.out.print("\rDownloading..." + currentPt + "%");
                System.out.flush();
            }
        }
        System.out.println("\rDownload complete " + currentSize + " / " + totalSize + " bytes");
        setLastDownloadedSize(currentSize);
        ((Activity) context).runOnUiThread(new Runnable() {
            @Override
            public void run() {
                TextView progressBar = (TextView) ((Activity)context).findViewById(R.id.progressBar);
                progressBar.setText("Download complete " + getLastDownloadedSize() + " bytes");
            }
        });

        if (out != null)
        {
            out.close();
            setDownloading(false);
            return null;
        }

        return totalBuffer.array();
    }
    
    private void sendMsg(String msg)
    {
        try
        {
            System.out.print("Sending " + msg + " ...");
            
            DataOutputStream out = new DataOutputStream(socket.getOutputStream());
            
            byte[] data = msg.getBytes();
            byte[] bSize = bSize(data.length);

            out.write(bSize);
            out.write(data);
            
            out.flush();

            System.out.println("ok");
        }
        catch (IOException e)
        {
            e.printStackTrace();
        }
    }

    private void connectTask()
    {
        System.out.print("Connecting to Socket Server...");
        System.out.flush();
        ((Activity) context).runOnUiThread(new Runnable() {
            @Override
            public void run() {
                TextView connectStatus = (TextView) ((Activity)context).findViewById(R.id.connectionStatus);
                connectStatus.setText("Trying to connect...");
            }
        });
        try
        {
            socket = new Socket();
            socket.connect(new InetSocketAddress(serverIp, PORT), 3000);
            
            byte[] serverReply = receive(new DataInputStream(socket.getInputStream()), null);
            String msg = new String(serverReply);
            if (!msg.equals(CONNECTION_RECEIVED))
            {
                socket.close();
                socket = null;
                
                System.out.println("fail");
                System.out.println("Server reply: " + msg);
            }
            else 
            {
                System.out.println("ok");
            }
            System.out.flush();
        }
        catch (SocketTimeoutException | UnknownHostException | java.net.ConnectException e)
        {
            System.out.println("fail");

            socket = null;

            if (serverIp != null)
                System.out.printf("Unable to connect to socket server at %s:%d\n", serverIp, PORT);
            else 
                System.out.println("Unable to connect to unknown host and port");
            
            System.out.flush();
        }
        catch (IOException e)
        {
            e.printStackTrace();
        }
        
        ((Activity) context).runOnUiThread(new Runnable() {
            @Override
            public void run() {
                TextView connectStatus = (TextView) ((Activity)context).findViewById(R.id.connectionStatus);
                if (socket != null)
                    connectStatus.setText("Connection established");
                else
                    connectStatus.setText("Connection not established");
            }
        });
    }

    protected void connect(String ip) throws IOException
    {
        if (socket != null) 
            disconnect();
        
        setServerIp(ip);    
        
        if (serverIp != null)
            new ConnectTask().execute(this);
    }

    protected void disconnect() throws IOException
    {
        if (socket != null)
        {
            sendMsg(CONNECTION_END);
            socket.close();
            socket = null;
        }
        setServerIp(null);
        ((Activity) context).runOnUiThread(new Runnable() {
            @Override
            public void run() {
                TextView connectStatus = (TextView) ((Activity)context).findViewById(R.id.connectionStatus);
                connectStatus.setText("Disconnected");
            }
        });
    }

    protected void download(int num)
    {
        new DownloadTask().execute(num);
    }

    protected void downloadAll()
    {
        try
        {
            sendMsg(REQUEST_FILE_COUNT);
            byte[] serverReply = receive(new DataInputStream(socket.getInputStream()), null);
            String msg = new String(serverReply);
            System.out.printf("Server reply (%d bytes): %s\n", serverReply.length, msg);
            System.out.flush();
            try
            {
                int fileCount = totalFilesToDownload = Integer.parseInt(msg);
                for (int i = 0; i < fileCount; ++i)
                {
                    download(i);
                    currFilesDownloaded = i + 1;
                    ((Activity) context).runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            TextView connectStatus = (TextView) ((Activity)context).findViewById(R.id.connectionStatus);
                            if (socket != null)
                                connectStatus.setText(currFilesDownloaded + " / " + totalFilesToDownload + " files downloaded");
                        }
                    });
                }
                ((Activity) context).runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        TextView progressBar = (TextView) ((Activity)context).findViewById(R.id.progressBar);
                        progressBar.setText("Download complete");
                    }
                });
            }
            catch (NumberFormatException e)
            {
                System.out.println("Unable to download all files. Not a valid file count: " + msg);
            }
        }
        catch (IOException e)
        {
            e.printStackTrace();
        }
    }

    protected String getFileList()
    {
        try 
        {
            sendMsg(REQUEST_FILE_LIST);
            byte[] serverReply = receive(new DataInputStream(socket.getInputStream()), null);
            System.out.printf("Server reply (%d bytes): %s\n", serverReply.length, new String(serverReply));
            System.out.flush();
            return new String(serverReply);
        } 
        catch (IOException e)
        {
            //e.printStackTrace();
        }
        return null;
    }

    protected boolean connectionEstablished()
    {
        return socket != null;
    }

    protected void setServerIp(String ip) { serverIp = ip; }

    protected String getServerIp() { return serverIp; }

    protected void setContext(Context context) { this.context = context; }

    protected Context getContext() { return context; }
    
    protected void setDownloadPt(int pt) { downloadPt = pt; }

    protected int getDownloadPt() { return downloadPt; }

    protected void setLastDownloadedSize(long size) { lastDownloadedSize = size; }

    protected long getLastDownloadedSize() { return lastDownloadedSize; }

    protected void setDownloading(boolean state) { downloading = state; }

    protected boolean getDownloading() { return downloading; }
}
