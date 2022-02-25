


import java.sql.Connection;
import java.sql.Statement;
import javax.swing.JOptionPane;
import java.sql.DriverManager;
import java.sql.SQLException;

public class Main {
    
    private static final String DRIVER = "com.mysql.cj.jdbc.Driver";
    private static final String URL = "jdbc:mysql://localhost:3306/boabiblioteca";
    private static final String USER = "root";
    private static final String PASS = "admin";

    public static void main(String[] args) {
        try {
            Connection con;
            Statement st;
            Class.forName(DRIVER);
            con = DriverManager.getConnection(URL, USER, PASS);
            String myInsert = "INSERT INTO livro(isbn, nome, autor, categoria, ano, editora) VALUES ('1234','a','a','a',2022,'a')";
            st = con.createStatement();
            st.executeUpdate(myInsert);
            JOptionPane.showMessageDialog(null, "Dados inseridos com sucesso");           
        } catch (ClassNotFoundException ex) {
            JOptionPane.showMessageDialog(null, "O Driver não está na biblioteca");
        } catch (SQLException ex) {
            JOptionPane.showMessageDialog(null, "Erro na conexão com o Banco de Dados");
        }
        
    }
}
