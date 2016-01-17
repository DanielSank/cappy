import scala.collection.mutable
import java.nio.charset.StandardCharsets.UTF_8
import spray.json._
import DefaultJsonProtocol._

/*
 * Take incoming bytes from the wire and return chunks representing
 * single json objects.
 */
class JsonDataStream {

  // val buffer = ...something...
  // A buffer of received bytes which weren't parsed into a complete json object yet.

  def processData(data: Array[Byte]): List[Array[Byte]] = {
    val result: List[Array[Byte]] = data :: Nil
    result
    // Dumb placeholder implementation which assumes the passed-in byte
    // array corresponds to exactly one flattened json object.
  }
}


class Referenceable {}


class Banana extends Referenceable {
  def mash: Unit = {
    println("Banana mashed!")
  }
}


class JsonProtocol {

  val stream = new JsonDataStream()
  val objects = mutable.Map[Int, Referenceable](0 -> new Banana)
  // Capabilities we've given out to other participants in the
  // system. For now we just hard code a Banana and we do not
  // hold different maps for different participants.

  def dataReceived(data: Array[Byte]): Unit = {
    val frames = stream.processData(data)  // endian-ness?
    frames.foreach(frame => handleFrame(frame))
  }

  def handleFrame(frame: Array[Byte]): Unit= {
    val jsObj = JsonParser(ParserInput(frame)).asJsObject()

    val targetId = jsObj.fields("targetId").convertTo[Int]
    val method = jsObj.fields("method").convertTo[String]
    // If "targetId" or "method" are not in the top level of the json data, this
    // call fails at run time.

    val target = objects(targetId)
    // if there is no Referenceable with id targetId, we fail here
    // at run time.

    val functionToCall = getattr(target, method)
    // This is janky python pseudocode that I don't know how to write in Scala.
    // I think we can sort of assume I can do this via a static lookup table
    // generated automatically by the IDL. Anyway note that this ought to be
    // a bound method of target.

    /*
     * Now we need to do something which in python would look like
     * this:
     * 
     *     parser = parsers(targetId)
     *     functionToCall(*parser(jsObj))
     */
  }
}


object QuickTest {
  def main(args: Array[String]): Unit = {
    val data = """{"target": 0, "args": {"x": 4, "y": "hello"}}"""
    val p = new JsonProtocol
    val ast = p.handleFrame(data.getBytes(UTF_8))
    println(s"Result: ${ast}")
    println(s"Which is a ${ast.getClass}")
    // The runtime type of ast is spray.json.JsonObject,
    // but the compiler says it's JsValue. Why is this
    // happening?
  }
}
