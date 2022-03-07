package model.conexao;

import java.sql.PreparedStatement;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.ResultSet;
import model.entities.Livro;

public class DAO {

    private static final String DRIVER = "com.mysql.cj.jdbc.Driver";
    private static final String URL = "jdbc:mysql://localhost:3306/boabiblioteca";
    private static final String USER = "root";
    private static final String PASS = "admin";
    Connection conn;
    PreparedStatement st;
    ResultSet res;

    public boolean conectar() {
        try {
            Class.forName(DRIVER);
            conn = DriverManager.getConnection(URL, USER, PASS);
            return true;
        } catch (ClassNotFoundException | SQLException ex) {
            throw new RuntimeException("Erro na conexão: ", ex);
        }
    }

    public void desconectar() {
        try {
            conn.close();
        } catch (SQLException ex) {
        }
    }

    public int salvar(Livro livro) {
        int status;
        try {                     
            st = conn.prepareStatement("INSERT INTO livro VALUES (?, ?, ?, ?, ?, ?)");
            st.setString(1, livro.getISBN());
            st.setString(2, livro.getTitulo());
            st.setString(3, livro.getAutor());
            st.setString(4, livro.getCategoria());
            st.setString(5, livro.getAno());
            st.setString(6, livro.getEditora());

            status = st.executeUpdate();
            return status;

        } catch (SQLException ex) {
            return ex.getErrorCode();
        }
    }

    public Livro consultarLivro(String ISBN){
        try {
            Livro livro = new Livro();
            st = conn.prepareStatement("SELECT * FROM livro WHERE ISBN = ?");
            st.setString(1, ISBN);
            res = st.executeQuery();
            //verifica se a consulta encontrou o registro com o identificador informado
            if (res.next()) {
                livro.setISBN(res.getString("isbn"));
                livro.setTitulo(res.getString("nome"));
                livro.setAutor(res.getString("autor"));
                livro.setCategoria(res.getString("categoria"));
                livro.setAno(res.getString("ano"));
                livro.setEditora(res.getString("editora"));
                return livro;
            } else {
                return null;
            }
        } catch (SQLException ex) {
            return null;
        } 
    }
    
    
    
}
