using System;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;

public class SynchronousSocketListener
{

    // Incoming data from the client.
    private static string data;

    public static void StartListening()
    {
        Int32 port = 11000;
        IPAddress address = Dns.GetHostAddresses(Dns.GetHostName())
                               .First(a => a.AddressFamily == AddressFamily.InterNetwork);
        IPEndPoint localEndPoint = new IPEndPoint(address, port);

        System.Console.WriteLine("IP: " + address + ", port: " + port);

        // Create a TCP/IP socket.
        Socket listener = new Socket(AddressFamily.InterNetwork,
                                     SocketType.Stream,
                                     ProtocolType.Tcp);

        // Bind the socket to the local endpoint and 
        // listen for incoming connections.
        try
        {
            listener.Bind(localEndPoint);
            listener.Listen(10);

            // Start listening for connections.
            while (true)
            {
                Console.WriteLine("Waiting for a connection...");
                // Program is suspended while waiting for an incoming connection.
                Socket handler = listener.Accept();
                data = null;

                // An incoming connection needs to be processed.
                while (true)
                {
                    byte[] bytes = new byte[1];
                    int bytesReceived = handler.Receive(bytes);
                    
                    data += Encoding.ASCII.GetString(bytes, 0, bytesReceived);
                    if (data.Contains("<EOF>"))
                    {
                        break;
                    }
                }

                // Show the data on the console.
                Console.WriteLine("Text received : {0}", data);

                // Echo the data back to the client.
                byte[] msg = Encoding.ASCII.GetBytes(data);

                handler.Send(msg);
                handler.Shutdown(SocketShutdown.Both);
                handler.Close();
            }


        }
        catch (Exception e)
        {
            Console.WriteLine(e.ToString());
        }

        Console.WriteLine("\nPress ENTER to continue...");
        Console.Read();
    }

    public static int Main(String[] args)
    {
        StartListening();
        return 0;
    }
}
