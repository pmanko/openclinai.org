import java.net.HttpURLConnection;
import java.net.URL;

public class HealthCheck {
  public static void main(String[] args) throws Exception {
    HttpURLConnection conn =
        (HttpURLConnection) new URL("http://127.0.0.1:8080/actuator/health").openConnection();
    conn.setConnectTimeout(3000);
    conn.setReadTimeout(3000);
    System.exit(conn.getResponseCode() == 200 ? 0 : 1);
  }
}
