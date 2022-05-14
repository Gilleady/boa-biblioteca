/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package model;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

/**
 *
 * @author gille
 */
public class LivroDAO {

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

    public int salvarLivro(Livro livro) {
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

    public int editarLivro(Livro livro) {
        int status;
        try {
            st = conn.prepareStatement("UPDATE livro SET nome = ?, autor = ?, categoria = ?, ano = ?, editora = ? WHERE isbn = ?");
            st.setString(1, livro.getTitulo());
            st.setString(2, livro.getAutor());
            st.setString(3, livro.getCategoria());
            st.setString(4, livro.getAno());
            st.setString(5, livro.getEditora());
            st.setString(6, livro.getISBN());

            status = st.executeUpdate();
            return status;

        } catch (SQLException ex) {
            return ex.getErrorCode();
        }
    }

    public List<Livro> listarLivros() {
        try {
            List<Livro> lista = new ArrayList<>();
            st = conn.prepareStatement("SELECT * FROM livro");
            res = st.executeQuery();
            //verifica se a consulta encontrou o registro com o identificador informado

            while (res.next()) {
                Livro livro = new Livro(
                        res.getString("isbn"),
                        res.getString("nome"),
                        res.getString("autor"),
                        res.getString("categoria"),
                        res.getString("ano"),
                        res.getString("editora"),
                        res.getInt("qtd_copias")
                );

                lista.add(livro);
            }
            return lista;

        } catch (SQLException ex) {
            return null;
        }
    }

    public List<Livro> pesquisarLivro(String pesquisa) {
        try {
            List<Livro> lista = new ArrayList<>();
            st = conn.prepareStatement("SELECT * FROM livro WHERE isbn LIKE ? OR nome LIKE ?");
            st.setString(1, pesquisa + "%");
            st.setString(2, pesquisa + "%");
            res = st.executeQuery();
            //verifica se a consulta encontrou o registro com o identificador informado

            while (res.next()) {
                Livro livro = new Livro(
                        res.getString("isbn"),
                        res.getString("nome"),
                        res.getString("autor"),
                        res.getString("categoria"),
                        res.getString("ano"),
                        res.getString("editora"),
                        res.getInt("qtd_copias")
                );

                lista.add(livro);
            }
            return lista;

        } catch (SQLException ex) {
            return null;
        }
    }

    public int excluirLivro(String isbn) {
        try {
            int status;
            st = conn.prepareStatement("DELETE FROM livro WHERE isbn = ?");
            st.setString(1, isbn);
            status = st.executeUpdate();

            return status;
        } catch (SQLException ex) {
            return ex.getErrorCode();
        }
    }
}
