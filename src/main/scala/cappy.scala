import java.nio.charset.StandardCharsets.UTF_8
import spray.json._


/*
 * Take incoming bytes from the wire and return chunks representing
 * single json objects.
 */
class JsonDataStream {
  def processData(data: Array[Byte]): List[Array[Byte]] = {
    val result: List[Array[Byte]] = data :: Nil
    result
    // Dumb placeholder implementation which assumes the passed-in byte
    // array corresponds to exactly one flattened json object.
  }
}


class JsonProtocol {

  val stream = new JsonDataStream()

  def dataReceived(data: Array[Byte]): Unit = {
    val frames = stream.processData(data)  // endian-ness?
    frames.foreach(frame => handleFrame(frame))
  }

  def handleFrame(frame: Array[Byte]): JsValue = {
    val ast = JsonParser(ParserInput(frame))
    ast
  }
}


object QuickTest {
  def main(args: Array[String]): Unit = {
    val data = """{"name": "Daniel"}"""
    val p = new JsonProtocol
    val ast = p.handleFrame(data.getBytes(UTF_8))
    println(s"Result: ${ast}")
    println(s"Which is a ${ast.getClass}")
    // The runtime type of ast is spray.json.JsonObject,
    // but the compiler says it's JsValue. Why is this
    // happening?
  }
}
