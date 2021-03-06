package dal;

import java.sql.PreparedStatement;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;
import javax.swing.JOptionPane;
import model.entities.Livro;
import model.entities.Pessoa;
import model.entities.Usuario;
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

    public int salvarUsuario(Usuario usuario) {
        int status;
        try {
            st = conn.prepareStatement("INSERT INTO login_usuario(nome, senha) VALUES (?, ?)");

            st.setString(1, usuario.getUsuario());
            st.setString(2, usuario.getSenha());
            //st.setString(3, usuario.getCpf());
            status = st.executeUpdate();
            return status;

        } catch (SQLException ex) {
            return ex.getErrorCode();
        }
    }

    public String entrar(Usuario usuario) {
        String status;
        try {
            st = conn.prepareStatement("SELECT * FROM login_usuario WHERE nome = ?");
            st.setString(1, usuario.getUsuario());
            res = st.executeQuery();

            if (res.next()) {
                if (usuario.getSenha().equals(res.getString("senha"))) {
                    status = "Logado com sucesso";
                } else {
                    status = "Senha incorreta";
                }
            } else {
                status = "Usuário não encontrado";
            }
        } catch (SQLException ex) {
            status = String.valueOf(ex);
        }
        return status;
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
                Livro livro = new Livro();
                livro.setISBN(res.getString("isbn"));
                livro.setTitulo(res.getString("nome"));
                livro.setAutor(res.getString("autor"));
                livro.setCategoria(res.getString("categoria"));
                livro.setAno(res.getString("ano"));
                livro.setEditora(res.getString("editora"));

                lista.add(livro);
            }
            return lista;

        } catch (SQLException ex) {
            return null;
        }
    }

    //A CONCLUIR - PARA PESQUISA PELA BARRA
    public ResultSet pesquisarLivro(String pesquisa) {
        try {
            st = conn.prepareStatement("SELECT * FROM livro WHERE isbn LIKE ? OR nome LIKE ?");
            st.setString(1, pesquisa + "%");
            st.setString(2, pesquisa + "%");
            res = st.executeQuery();
            return res;

        } catch (SQLException ex) {
            JOptionPane.showMessageDialog(null, ex);
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

    public int salvarPessoa(Pessoa p) {
        int status;
        try {
            st = conn.prepareStatement("INSERT INTO cliente(cpf, nome, rg) VALUES (?, ?, ?)");
            st.setString(1, p.getCpf());
            st.setString(2, p.getNome());
            st.setString(3, p.getRg());
            //st.setDate(4, (Date) p.getData_nascimento());

            status = st.executeUpdate();
            return status;

        } catch (SQLException ex) {
            return ex.getErrorCode();
        }
    }

    public List<Pessoa> listarPessoas() {
        try {
            List<Pessoa> lista = new ArrayList<>();
            st = conn.prepareStatement("SELECT * FROM cliente");
            res = st.executeQuery();
            //verifica se a consulta encontrou o registro com o identificador informado

            while (res.next()) {
                Pessoa p = new Pessoa();
                p.setCpf(res.getString("cpf"));
                p.setNome(res.getString("nome"));
                p.setRg(res.getString("rg"));

                lista.add(p);
            }
            return lista;

        } catch (SQLException ex) {
            return null;
        }
    }
}
