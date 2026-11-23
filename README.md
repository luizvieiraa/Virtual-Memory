# Implementação 7 - Memória virtual

Autor: Luiz Vieira. Identificador de entrega: `lhcv`.

Simulador em C11 com 256 páginas lógicas, páginas de 256 bytes, 128 frames
físicos e TLB de 16 entradas. As políticas FIFO e LRU são independentes para
páginas e TLB. A busca na TLB usa 16 threads POSIX por endereço, uma por entrada.
O enunciado traz "Implementação 6" no cabeçalho; esta é a atividade 7 - VM.

## Compilar e executar

Em Linux, Unix ou macOS, use um compilador C com POSIX threads e Make:

```sh
make
./vm addresses.txt lru fifo
make clean
```

Execute `make` na raiz deste repositório. O primeiro argumento é o arquivo de
endereços; o segundo escolhe a política de páginas e o terceiro a da TLB.
Cada política aceita exatamente `fifo` ou `lru`, em minúsculas.

Coloque `BACKING_STORE.bin` no diretório de execução. O arquivo original deve
conter as 256 páginas (65.536 bytes). Os anexos do professor não são versionados.
O arquivo de entrada contém um inteiro decimal de 0 a 65535 por linha; espaços
nas extremidades são aceitos. Arquivos vazios e linhas vazias são rejeitados.

O programa gera **`correct.txt` no diretório de execução**, sobrescrevendo a
saída anterior. Guarde o gabarito do professor com outro nome, por exemplo
`gabarito.txt`. A saída tem este formato:

```text
Virtual address: 16916 TLB: 0 Physical address: 20 Value: 0
```

O valor acima é o exemplo do gabarito e depende do binário original. `TLB` indica
o índice da entrada usada, inclusive quando a tradução acabou de ser inserida.
Ao final são escritos o total de endereços, page faults, taxa de page faults,
hits da TLB e taxa de hits, com três casas decimais nas taxas.

```sh
./vm addresses.txt lru fifo
diff -u gabarito.txt correct.txt
```

Uma execução bem-sucedida retorna 0. Erros retornam valor diferente de 0 e
mensagem em stderr: argumentos inválidos, arquivo ausente, entrada malformada,
página incompleta, falha na saída ou criação de threads. Uma saída parcial de
execução que falhou não deve ser usada como resultado válido.

## Organização e algoritmos

`vm.c` concentra a leitura, tradução, substituição e busca paralela. O endereço
é decomposto em `página = endereço / 256` e `deslocamento = endereço % 256`.
Os frames livres são preenchidos em ordem de 0 a 127. Em page fault, a página
é lida na posição `página * 256` do backing store. A tradução física é
`frame * 256 + deslocamento`; o byte é convertido para o intervalo -128 a 127.

FIFO de páginas mantém um índice circular de vítima, atualizado apenas nas
substituições. LRU mantém posições de recência limitadas a 0..127 e atualiza
a ordem em todo acesso, incluindo hits da TLB. Ao remover uma página, seu
mapeamento na tabela e qualquer entrada correspondente na TLB são invalidados.

A TLB preenche a primeira entrada livre. Quando cheia, remove a de menor
marcador: inserção para FIFO, último acesso para LRU. As threads recebem cópias
das entradas e resultados separados; a principal aguarda todas com
`pthread_join` antes de atualizar qualquer estrutura. A busca paralela é uma
simulação didática: criar 16 threads por acesso pode custar mais que uma busca
sequencial de 16 entradas; não é alegada melhoria de desempenho.

## Testes e evidências

Python 3 é necessário somente para os testes e o empacotamento:

```sh
make test
python3 tests/test_vm.py --addresses addresses.txt --reference gabarito.txt --backing BACKING_STORE.bin
```

Os testes geram dados sintéticos em diretórios temporários e comparam toda a
saída das quatro combinações com um modelo independente. Cobrem valores com
sinal, limites, hits, misses, recência, invalidação, substituições e erros.
Sem `--backing`, a comparação opcional com o professor usa bytes zerados e
exclui o campo `Value`: isso valida mapeamentos e estatísticas, não os bytes.

Consulte `evidencias.log` para os resultados efetivamente obtidos. A referência
`lru fifo` tem 1000 traduções, 539 page faults (0.539) e 54 hits (0.054).
A comparação desses campos passou. A validação dos valores com o binário
original permanece pendente, pois o arquivo não estava disponível.

No Windows com MinGW-w64 e winpthreads, a compilação também foi testada:

```powershell
mingw32-make -B CC=gcc
python tests/test_vm.py --executable ./vm.exe
mingw32-make clean RM="cmd /c del /Q"
```

Linux foi validado no Ubuntu via WSL. Unix e macOS não foram executados.
Ao alternar entre Windows e WSL no mesmo diretório, limpe ou force a
recompilação: os executáveis de cada sistema têm formatos diferentes.

## Entrega

```sh
make package
tar -tf lhcv.tar
```

O pacote contém somente `lhcv/vm.c` e `lhcv/Makefile`, conforme o enunciado.
Após extrair, entre em `lhcv/` e execute `make`. O alvo padrão não depende de
Python. Os alvos opcionais `test` e `package` exigem os arquivos auxiliares
disponíveis no repositório completo.

- GitHub: `vm.c`, `Makefile`, este README, `evidencias.log`, `lhcv.pdf`, testes
  e scripts auxiliares. Os commits anteriores preservam as versões por etapa.
- Classroom: enviar **`lhcv.pdf` e `lhcv.tar` separadamente**.
- Não incluir executáveis, anexos do professor ou `correct.txt` no `.tar`.

Não foi realizado envio ao Classroom nem push automático.
